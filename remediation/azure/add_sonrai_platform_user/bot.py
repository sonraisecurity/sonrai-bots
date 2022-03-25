import logging
import sys
import re
import time
import json

def run(ctx):
    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')
    ticket_srn = ticket.get('srn')

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    #query ticket endpoint for swimlanes
    queryTicketsForSwimlanes = ('''
    {
      Tickets
        (where: { srn: {op:EQ, value:"'''+ ticket_srn + '''"}}) 
              {
          items {
            swimlaneSRNs
          }
        }
      }
    ''')
    variables = { }
    logging.info('Searching for swimlanes of ticket {}'.format(ticket_srn))
    r_ticket_swimlanes = graphql_client.query(queryTicketsForSwimlanes, variables)

    swimlaneList = r_ticket_swimlanes['Tickets']['items'][0]['swimlaneSRNs']

    # get resourceIDs of the Swimlanes of the tickets
    querySwimlanes =('''
    query Swimlanes ($swimlaneSRNs: [String]){Swimlanes 
        (where: 
               {srn: {op:IN_LIST, values:$swimlaneSRNs}}
        )
      {
            items {
                  resourceId
        }}}
    ''')

    #Build the variable to use the query

    variables = ('{"swimlaneSRNs": [')
    for resourceId in swimlaneList:
        variables += '"'+resourceId+'",'

    variables = variables[ : -1]
    variables += ']}'

    logging.info('Searching for resourceIds of swimlanes {}'.format(swimlaneList))
    r_swimlanes = graphql_client.query(querySwimlanes, variables)

    group_srns = None

    # Loop through each of the custom fields and set the values that we need
    for customField in ticket.get('customFields'):
        if 'value' not in customField.keys():
            continue

        name = customField['name']
        value = customField['value']

        if name == 'AD Group':
            group_srns = value.strip('][').split(',')

    # Built query for groups
    group_filter = ""
    for srn in group_srns:
       #get each individual group and put in the proper format to work in the graphQL below
       group_filter += ('{srn: { op:CONTAINS, value: '+srn+'}}')

    #GraphQL query for the groups
    queryADUsersByGroup = ('''
    query ActiveDirectoryUsersInGroup {
  Users(
    where: {
      and: [
        {
          and: [
            { active: { op: EQ, value: true } }
            { type: { op: EQ, value: ActiveDirectoryUser } }
          ]
        }
        {
          isMemberOf: {
            count: { op: GT, value: 0 }
            items: {
              and: [
                {
                  or: [ '''
                   + group_filter +
                  ''']
                }
                {}
              ]
            }
          }
        }
      ]
    }
  ) {
    count
    items {
      userName
      name
    }
  }
}
    ''')

    # get emails, names from AD groups
    variables = { }
    logging.info('Searching for users in AD groups: {}'.format(group_srns))
    r_AD_query = graphql_client.query(queryADUsersByGroup, variables)

    # Query for the current users of the platform
    querySonraiUsers = 'query sonraiusers{SonraiUsers {items{ email } } }'
    variables = { }
    logging.info('Searching for existing Platform users')
    r_platform_users = graphql_client.query(querySonraiUsers, variables)

    # Query for users on the invite list
    querySonraiInvites = 'query sonraiinvites{SonraiInvites {items {email} } }'
    variables = { }
    logging.info('Searching for users already invited')
    r_invited_users = graphql_client.query(querySonraiInvites, variables)

    # Only allowing this script to assign "Data Viewer" role
    role = "srn:supersonrai::SonraiRole/DataViewer"

    #build pendingRolesAssigners from role and swimlanes
    pending_role_assigners = '"pendingRoleAssigners":[ '
    for sw in r_swimlanes['Swimlanes']['items']:
        pending_role_assigners += ( '{"roleSrn": "'+role+'",')
        pending_role_assigners += ( '"scope": "'+sw['resourceId']+'"},')

    #remove the last comma from the pending role assigners
    pending_role_assigners = pending_role_assigners[ : -1]
    pending_role_assigners += ']'

    # invite user mutation
    mutation_invite = '''mutation inviteUser($input: [SonraiInviteCreator!]!) {
    CreateSonraiInvites(input: $input) {
      items { srn resourceId email dateSent expiry isPending pendingRoleAssignments 
      { items { srn role { items { srn name }} scope } } } } }'''


    for email in r_AD_query['Users']['items']:
        invite_user = True

        #check if the userName is in the invite list
        for already_invited in r_invited_users['SonraiInvites']['items']:
           if email['userName'] == already_invited['email']:
               invite_user = False

        #check if the userName is in the platform user list
        for already_added in r_platform_users['SonraiUsers']['items']:
            if email['userName'] == already_added['email']:
                invite_user = False

        if invite_user:
            variables = ( '{ "input" : { ' +
                          '"email":"' +email['userName']+ '",'
                          '"name":"' + email['name'] + '",' +
                          pending_role_assigners +
                          '} }')
            logging.info('inviting users {}'.format(email['userName']))
            r_create_invite = graphql_client.query(mutation_invite, variables)
