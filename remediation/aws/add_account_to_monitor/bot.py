import logging
import sys
import re
import time
from datetime import datetime, timedelta

def run(ctx):
    #CONSTANTS
    _maxAccountsToAdd = 10
    _snoozeInterval = 2 #hours

    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')
    currentTime = round(time.time() * 1000)
    now = datetime.now()
    dateStamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    role_name = None
    bot_role_name = None
    default_collector_srn = None

    # Loop through each of the custom fields and set the values that we need
    for customField in ticket.get('customFields'):
        if 'value' not in customField.keys():
            continue

        name = customField['name']
        value = customField['value']

        if name == 'Role Name':
            role_name = value
        elif name == 'Bot Role Name':
            bot_role_name = value
        elif name == 'Collector':
            default_collector_srn = value

    #GraphQL query for the AWS accounts
    queryAllAccounts = ('''
    query Accounts {
      Accounts(
        where: {
          cloudType: { op: EQ, value: "aws" }
          type: { op: IN_LIST, values: [AWSAccount] }
          tagSet: {
            op: NOT_CONTAINS
            value: "sonraiBotAdded"
            caseSensitive: false
          }
          tagSet:{
            op:CONTAINS
            value: "sonraiSwimlanes"
            caseSensitive: false
          }
        }
    ) {
      count
      items {
        account
        srn
        tagSet
      }
    }
  }
    ''')

    variables = { }
    logging.info('Searching for all AWS accounts')
    r_accounts = graphql_client.query(queryAllAccounts, variables)

    # GraphQL to get monitored AWS accounts on collector already
    queryPlatformAccounts = ('''query CloudAccounts {
  PlatformCloudAccounts
  (where:
    {
      cloudType: {value:"aws"}
    }
  )
  {
    count
    items {
      cloudType
      blob
    }
  }
}''')
    variables = { }
    logging.info('Searching for already monitored accounts on collector: {}'.format(default_collector_srn))
    r_platform_accounts = graphql_client.query(queryPlatformAccounts, variables)

    # mutation to add account
    mutation_add_account = '''
    mutation createSubAccount($account: PlatformcloudaccountCreator!) {
    CreatePlatformcloudaccount(value: $account) {srn blob cloudType  name }}'''

    # mutation for adding a processed tag to the account
    mutation_add_tag  = '''
       mutation addTagsWithNoDuplicates($key: String, $value: String, $srn: ID) {
       AddTag(value: {key: $key, value: $value, tagsEntity: {add: [$srn]}}) {srn key value }}
    '''

    # query for collector's SRN
    query_collector_srn = ('''
        query collectorSRN($name: String){
          PlatformAccounts
            (where: { 
              cloudType: { value: "aws" } 
              name: {op:EQ value:$name}
            }) {
              count
              items {
                srn 
              }
            }
          }
    ''')

    accountCount = 0
    swimlaneAccountList = dict()

    for item in r_accounts['Accounts']['items']:
        if accountCount >= _maxAccountsToAdd:
            # only adding _maxAccountsToAdd with each pass to prevent too many discoveries at once
            logging.WARN("maximum number of accounts added for this pass")
            break

        #step through all AWS accounts to see if it is already added to a collector
        add_account = True
        accountToAdd = item['account']
        account_srn = item['srn']

        #check if the accountToAdd is already added
        for existing_accounts in r_platform_accounts['PlatformCloudAccounts']['items']:
            account_number = existing_accounts['blob']['accountNumber']
            if accountToAdd == account_number:
                add_account = False

        if add_account:
            accountCount += 1 # this is for maximum number of accounts to be added

            for tag in item['tagSet']:
                # find which swimlanes to add account to, from the tags on the account
                if "sonraiSwimlanes" in tag:
                    swimlaneNames = tag.replace("sonraiSwimlanes:","")
                    for swimlane in swimlaneNames.split():
                        if swimlane in swimlaneAccountList:
                            swimlaneAccountList[swimlane].append(accountToAdd)
                        else:
                            swimlaneAccountList[swimlane] = [accountToAdd]
                elif "sonraiCollector" in tag:
                    # Account has a collector name tag, see if the name has a valid SRN
                    collectorName = tag.replace("sonraiCollector:","")
                    varCollector = ('{"name": "' + collectorName + '" }')
                    r_collector_srn = graphql_client.query(query_collector_srn, varCollector)
                    if r_collector_srn['PlatformAccounts']['count'] == 0:
                        # account doesn't have a valid collector name tag, use the default collector SRN from the custom ticket
                        collector_srn = default_collector_srn
                    else:
                        # account's tag has a valid collector name, use this SRN
                        collector_srn = r_collector_srn['PlatformAccounts']['items'][0]['srn']

            # AWS Account doesn't exist on the collector. Adding it here
            role_arn = ("arn:aws:iam::"+accountToAdd+":role/"+role_name)
            bot_role_arn = ("arn:aws:iam::"+accountToAdd+":role/"+bot_role_name)
            variables1 =  ('{"account": {"containedByAccount":' +
                                         '{"add": "' + collector_srn + '"},' +
                                     '"cloudType": "aws",' +
                                     '"blob": {'  +
                                         '"accountNumber": "' + accountToAdd +'",'+
                                         '"roleArn": "' + role_arn + '",' +
                                         '"botRoleArn": "' + bot_role_arn + '",' +
                                         '"runDateTime": ' + str(currentTime) +
                                         '}'+
                                     '}'+
                         '}')
            logging.info('Adding Account {} to collector {}'.format(accountToAdd,collector_srn))
            r_add_account = graphql_client.query(mutation_add_account, variables1)
            variables2 = ('{"key":"sonraiBotAdded","value":"'+ dateStamp + '","srn":"'+account_srn+'"}')
            r_add_tag = graphql_client.query(mutation_add_tag, variables2)


    # section for adding accounts to swimlanes
    query_find_swimlane_SRN = ('''
        query SwimlaneSRN($title: String) {
          Swimlanes(where: { title: { op: EQ, value: $title } }) {
            count
            items {
              srn
            }
          }
        }
    ''')
    mutation_add_to_swimlane = ('''
       mutation updateSwimlane($swimlane: SwimlaneUpdater!, $srn: ID!) {
        UpdateSwimlane(srn: $srn, value: $swimlane) {
          srn
        }
      }
    ''' )

    for swimlane in swimlaneAccountList:
        # find the swimlane's SRN from the swimlane's name
        variables1 = ('{"title": "' + swimlane + '" }')
        r_swimlane_srn = graphql_client.query(query_find_swimlane_SRN, variables1)

        # check if the swimlane exists
        if r_swimlane_srn['Swimlanes']['count'] == 0:
            # swimlane doesn't exist skip this one
            logging.warn(" Swimlane {} doesn't exist skipping.".format(swimlane))
            continue

        swimlaneSRN = r_swimlane_srn['Swimlanes']['items'][0]['srn']

        # build the variable for the add to swimlane mutation
        tmp_variables2 = ('{"srn": "' + swimlaneSRN + '",'+
                      '"swimlane": {' +
                            '"accounts": { "add": ' + str(swimlaneAccountList[swimlane]) + '}' +
                      '}' +
                      '}'
                      )
        variables2 = tmp_variables2.replace("'", "\"")

        # add the accounts to swimlane
        r_add_to_swimlane = graphql_client.query(mutation_add_to_swimlane, variables2)


    # un-snooze and re-snooze the ticket for a shorter time period
    mutation_reopen_ticket = ('''
      mutation openTicket($srn:String){
        ReopenTickets(input: {srns: [$srn]}) {
          successCount
          failureCount
        }
      }
    ''')
    mutation_snooze_ticket = ('''
        mutation snoozeTicket($srn: String, $snoozedUntil: DateTime) {
            SnoozeTickets(snoozedUntil: $snoozedUntil, input: {srns: [$srn]}) {
              successCount
              failureCount
              __typename
            }
          }
    ''')
    # calculate the snoozeUntil time
    snoozeUntil = datetime.now() + timedelta(hours=_snoozeInterval)
    variables = ('{"srn": "' + ticket['srn'] + '", "snoozedUntil": "' + str(snoozeUntil).replace(" ","T") + '" }')
    # re-open ticket so it can be snoozed again
    r_reopen_ticket = graphql_client.query(mutation_reopen_ticket, variables)
    # snooze ticket
    r_snooze_ticket = graphql_client.query(mutation_snooze_ticket, variables)

