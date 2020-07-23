import logging

from azure.graphrbac import GraphRbacManagementClient


def run(ctx):

    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    logging.info('deleting user: {}'.format(object_id))
    graphrbac_client.users.delete(upn_or_object_id=object_id)