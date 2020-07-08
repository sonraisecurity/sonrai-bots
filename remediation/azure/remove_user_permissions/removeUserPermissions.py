from azure.mgmt.authorization.v2018_09_01_preview import AuthorizationManagementClient
from azure.mgmt.authorization.v2015_06_01 import AuthorizationManagementClient as ClassicAdminAuthorizationClient


def run(ctx):

    # Get subscription id
    subscription_id = "2731df3f-27cc-4548-8d8d-8bc4ca3f8429"
    object_id = "df00ff51-32d7-4945-8477-9e56921adfce"
    user_email = "joshua.delete@sandybirdgmail.onmicrosoft.com"

    l

    classic_admin_authorization_client = ctx.get_client().get(ClassicAdminAuthorizationClient)
    classic_admin_authorization_client.config.subscription_id = subscription_id
    for x in classic_admin_authorization_client.classic_administrators.list():
        print(x)

    authorization_management_client = ctx.get_client().get(AuthorizationManagementClient)
    authorization_management_client.config.subscription_id = subscription_id
    filter = "assignedTo('{object_id}')".format(object_id=object_id)
    for x in authorization_management_client.role_assignments.list(filter=filter):
        print(x)


