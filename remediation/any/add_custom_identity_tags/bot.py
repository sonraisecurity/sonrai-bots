import logging
from datetime import datetime, timedelta

from query_loader import graphql_files, mutation_files

gql = graphql_files(cloud_type="Azure")
mut = mutation_files()


def run(ctx):
    _snooze_interval = 2  # hours

    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    query_variables = {}
    logging.info('Searching for Identities')
    results = graphql_client.query(gql['Identities.gql'], query_variables)
    data = results['Identities']['items']

    logging.info('Tagging Identities')
    for row in data:
        mutation_variables = ('{"tag_name":"sonraiIdentityTag","label_value":"' + str(row['label']) + '","srn":"' + str(row['srn']) + '"}')
        return_value = graphql_client.query(mut['labeltotag.mut'], mutation_variables)

        print("\nReturn Value of Mutation: ", return_value)

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
    snooze_until = datetime.now() + timedelta(hours=_snooze_interval)
    variables = ('{"srn": "' + ticket['srn'] + '", "snoozedUntil": "' + str(snooze_until).replace(" ", "T") + '" }')
    # re-open ticket so it can be snoozed again
    graphql_client.query(mutation_reopen_ticket, variables)
    # snooze ticket
    graphql_client.query(mutation_snooze_ticket, variables)
