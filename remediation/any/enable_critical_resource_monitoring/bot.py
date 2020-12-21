import logging


def run(ctx):
    object_srn = ctx.resource_srn

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # GraphQL query to enable critical resource monitoring (CRM) on the resource with the specified SRN
    query = '''
        mutation EnableCriticalResourceMonitoring($srn: String!) {
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

    # Enable CRM
    logging.info('enabling critical resource monitoring on: {}'.format(object_srn))
    graphql_client.query(query, variables)
