import logging

from azure.graphrbac import GraphRbacManagementClient


def run(ctx):

    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    logging.info('deleting Service Principal: {}'.format(object_id))
    graphrbac_client.service_principals.delete(object_id=object_id)