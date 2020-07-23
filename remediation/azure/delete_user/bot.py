import logging

from azure.graphrbac import GraphRbacManagementClient


def run(ctx):

    policy_evidence = ctx.get_evidence_policy()
    data = policy_evidence.get('data').get('Users').get('items')
    if data:
        data = data[0]

    object_id = data.get('resourceId')

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    logging.info('deleting user: {}'.format(object_id))
    graphrbac_client.users.delete(upn_or_object_id=object_id)