from sonrai.platform.azure.client import ManagedIdentityClient


def run(ctx):
    managed_identity_client = ctx.get_client().get(ManagedIdentityClient)

    # https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/how-to-manage-ua-identity-rest
    subscription_id = "2731df3f-27cc-4548-8d8d-8bc4ca3f8429"
    resource_group = "joshua-resource-group"
    user_assigned_identity_name = "joshua-managed-identity"

    managed_identity_client.delete(subscription_id=subscription_id, resource_group=resource_group, user_assigned_identity_name=user_assigned_identity_name)
