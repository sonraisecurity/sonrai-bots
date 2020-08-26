import logging


def run(ctx):
    object_srn = ctx.resource_srn

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # GraphQL query to enable change detection on resource with the specified SRN
    query = '''
        mutation EnableChangeDetection($srn: String!) {
          setMonitor(
            monitorStatusBySrn: [
              {
                srn: $srn,
                monitor: true
              }
            ]
          ) {
            srn
            monitor
          }
        }
    '''
    variables = {"srn": object_srn}

    # Enable change detection
    logging.info('enabling change detection on: {}'.format(object_srn))
    graphql_client.query(query, variables)




