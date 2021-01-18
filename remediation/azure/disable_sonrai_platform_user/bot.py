import logging
import re

def run(ctx):
    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

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
    querySonraiUsers = 'query sonraiusers{SonraiUsers {items{ srn email } } }'
    variables = { }
    logging.info('Searching for existing Platform users')
    r_platform_users = graphql_client.query(querySonraiUsers, variables)

    # invite user mutation
    mutation_disable = '''mutation disableSonraiUser($updateUser: [SonraiUserUpdater!]!) {
                          UpdateSonraiUsers(input: $updateUser) { items { srn } } }'''


    for active_user in r_platform_users['SonraiUsers']['items']:
        disable_user = True
        if active_user['email'] == 'support@sonraisecurity.com':
            #ignore this user since it is the bot user
            continue
        #check if the userName is in the platform user list
        for user_in_group in r_AD_query['Users']['items']:
            if active_user['email'] == user_in_group['userName']:
                disable_user = False

        if disable_user:
            variables = ( '{ "updateUser" : { ' +
                          '"srn":"' +active_user['srn']+ '",'
                          '"isActive":false} }')
            logging.info('disabling users {}'.format(active_user['email']))
            r_disable_user = graphql_client.query(mutation_disable, variables)