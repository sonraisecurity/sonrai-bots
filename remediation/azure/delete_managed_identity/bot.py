import logging

from sonrai.platform.azure.client import ManagedIdentityClient


def run(ctx):
    # Get data for bot from config
    config = ctx.config
    data = config.get('data')
    # https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/how-to-manage-ua-identity-rest
    subscription_id = data.get('subscriptionId')
    resource_group = data.get('resourceId')
    user_assigned_identity_name = data.get('userAssignedIdentityName')

    managed_identity_client = ctx.get_client().get(ManagedIdentityClient)

    logging.info('deleting managed identity: {} from subscription: {} and resource-group: {}'.format(user_assigned_identity_name, subscription_id, resource_group))
    managed_identity_client.delete(subscription_id=subscription_id, resource_group=resource_group,user_assigned_identity_name=user_assigned_identity_name)
