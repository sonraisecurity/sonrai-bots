import logging

from sonrai import gql_loader


def run(ctx):
    # create gql_loader queries
    gql = gql_loader.queries()

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # load results of saved search "BOT: Identities" - see graphql/Identities.sql as a sample of the saved search to create in the UI
    logging.info('Loading SavedSearch Results')
    data = gql_loader.saved_search(ctx, name="BOT: Identities")

    if data:
        logging.info('Tagging Identities Started')
        for row in data['Identities']['items']:
            mutation_variables = ('{"tag_name":"sonraiIdentityTag","label_value":"' + str(row['label']) + '","srn":"' + str(row['srn']) + '"}')
            return_value = graphql_client.query(gql['labeltotag.gql'], mutation_variables)

            print("\nReturn Value of Mutation: ", return_value)

        logging.info('Tagging Identities Completed')

    logging.info('Snoozing Ticket For 2 Hours')
    gql_loader.snooze_ticket(ctx, hours=2)
