import logging
import json
from sonrai import gql_loader
import datetime

today = datetime.datetime.now()
today = today.strftime("%B %d %Y")

def run(ctx):
    # Load searches:
    gql = gql_loader.queries()

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # Get the ticket data from the context
    ticket = ctx.config
    ticketSrn = ticket['data']['ticket']['srn']
    ticketSrn = ('{"srn": "' + ticketSrn + '" }')

    #Set query/mutation variables
    get_resources = None
    query_resourcesToExempt = gql['savedQuery.gql']
    mutation_setImportance = gql['setImportance.gql']
    query_ticket = gql['ticket.gql']
    mutation_tag = gql['tag.gql']

    #Ticket look up to get custom fields
    customField = graphql_client.query(query_ticket,ticketSrn)

    #Format search name for custom search query
    search_name = customField['ListFindings']['items'][0]['cfFields'][0]['value']
    search_name = ('{"name": "' + search_name + '" }')

    #Run custom search query to get resources to exempt
    get_resources = graphql_client.query(query_resourcesToExempt,search_name)

    #exempt the resources
    for resource in get_resources['ExecuteSavedQuery']['Query']['Resources']['items']:
        srn = resource['srn']
        variables = ('{"value":"' + today + '","srn":"' + srn + '"}')
        srn = ('{"srn": "' + srn + '" }')
        set_importance = graphql_client.query(mutation_setImportance, srn)
        graphql_client.query(mutation_tag, variables)
        endResource = set_importance['setImportance']['srn']
        logging.info('Exempted and Tagged Resource: ' + endResource)

    gql_loader.snooze_ticket(ctx, hours=24)
