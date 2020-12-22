import logging
import sys
import re
import time
from datetime import datetime

def run(ctx):
    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')
    currentTime = round(time.time() * 1000)
    now = datetime.now()
    dateStamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    role_name = None
    bot_role_name = None
    collector_srn = None

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
            collector_srn = value

    #GraphQL query for the AWS accounts
    queryAllAccounts = ('''
    query Accounts {
      Accounts(
        where: {
          cloudType: { op: EQ, value: "aws" }
          type: { op: IN_LIST, values: [AWSAccount] }
          tagSet: {
            op: NOT_CONTAINS
            value: "SonraiBotAdded"
            caseSensitive: false
          }
        }
    ) {
      count
      items {
        account
        srn
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
    logging.info('Searching for already monitored accounts on collector: {}'.format(collector_srn))
    r_platform_accounts = graphql_client.query(queryPlatformAccounts, variables)

    # mutation to add account
    mutation_add_account = ''' 
    mutation createSubAccount($account: PlatformcloudaccountCreator!) {
    CreatePlatformcloudaccount(value: $account) {srn blob cloudType  name }}'''

    mutation_add_tag  = '''
       mutation addTagsWithNoDuplicates($key: String, $value: String, $srn: ID) {
       AddTag(value: {key: $key, value: $value, tagsEntity: {add: [$srn]}}) {srn key value }} 
    '''


    for item in r_accounts['Accounts']['items']:
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
            # AWS Account doesn't exist on the collector. Adding it here
            role_arn = ("arn:aws:iam::"+accountToAdd+":role/"+role_name)
            bot_role_arn = ("arn:aws:iam::"+accountToAdd+":role/"+bot_role_name)
            variables =  ('{"account": {"containedByAccount":' +
                                         '{"add": "' + collector_srn + '"},' +
                                     '"cloudType": "azure",' +
                                     '"blob": {'  +
                                         '"accountNumber": "' + accountToAdd +'",'+
                                         '"roleArn": "' + role_arn + '",' +
                                         '"botRoleArn": "' + bot_role_arn + '",' +
                                         '"runDateTime": ' + str(currentTime) +
                                         '}'+
                                     '}'+
                         '}')
            logging.info('Adding Account {}'.format(accountToAdd))
            r_add_account = graphql_client.query(mutation_add_account, variables)
            variables = ('{"key":"SonraiBotAdded","value":"'+ dateStamp + '","srn":"'+account_srn+'"}')
            r_add_tag = graphql_client.query(mutation_add_tag, variables)
