import logging

from sonrai.platform.azure.resource import ParsedResourceId
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from msrestazure.azure_active_directory import AADTokenCredentials

def run(ctx):
    resource_id = ParsedResourceId(ctx.resource_id) \
        .assert_provider('Microsoft.DBforPostgreSQL') \
        .assert_type("servers")
    client = ctx.get_client().get(PostgreSQLManagementClient, subscription_id=resource_id.subscription)
    logging.info("[{}] Enabling log_connections".format(resource_id))
    client.configurations.create_or_update(
        resource_group_name=resource_id.resource_group,
        server_name = resource_id.name,
        configuration_name='log_connections',
        value='on')
    logging.debug("[{}] Enabled log_connections".format(resource_id))
