import logging

from azure.mgmt.authorization.v2018_09_01_preview import AuthorizationManagementClient

def run(ctx):

    # Get data
    config = ctx.config
    data = config.get('data').get('data')
    subscription_id = data.get('subscriptionId')
    object_id = data.get('objectId')

    logging.info('removing user permissions from user: {} in subscription: {}'.format(object_id, subscription_id))
    authorization_management_client = ctx.get_client().get(AuthorizationManagementClient)
    authorization_management_client.config.subscription_id = subscription_id
    filter = "assignedTo('{object_id}')".format(object_id=object_id)
    for role_assignment in authorization_management_client.role_assignments.list(filter=filter):
        authorization_management_client.role_assignments.delete_by_id(role_id=role_assignment.id)


