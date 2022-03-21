from os import listdir
from os.path import isfile, join

queriesDirectory = 'queries'
query_files = [f for f in listdir(queriesDirectory) if isfile(join(queriesDirectory, f))]


# GQL queries
def graphql_files(**kwargs):
    gql = dict()

    for file in query_files:
        if file.endswith('.gql'):
            file_content = open("{0}/{1}".format(queriesDirectory, file))
            gql_data = file_content.read()

            # Iterating over the keys of the Python kwargs dictionary
            for key, value in kwargs.items():
                gql_data = gql_data.replace('$' + key, value)

            gql[file] = gql_data

    return gql


def mutation_files(**kwargs):
    mut = dict()

    for file in query_files:
        if file.endswith('.mut'):
            file_content = open("{0}/{1}".format(queriesDirectory, file))
            mut_data = file_content.read()

            # Iterating over the keys of the Python kwargs dictionary
            for key, value in kwargs.items():
                mut_data = mut_data.replace('$' + key, value)

            mut[file] = mut_data

    return mut
