import logging

from query_loader import graphql_files, mutation_files

gql = graphql_files(cloud_type="Azure")
mut = mutation_files()


def run(ctx):
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
