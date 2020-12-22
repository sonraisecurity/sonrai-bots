import logging

from sonrai.platform.azure.resource import ParsedResourceId
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient

def run(ctx):
    resource_id = ParsedResourceId(ctx.resource_id) \
        .assert_provider('Microsoft.DBforPostgreSQL') \
        .assert_type("servers")
    client = ctx.get_client().get(PostgreSQLManagementClient, subscription_id=resource_id.subscription)
    logging.info("[{}] Setting log_retention_days to: {}".format(resource_id, _LOG_RETENTION_DAYS))
    client.configurations.create_or_update(
        resource_group_name=resource_id.resource_group,
        server_name = resource_id.name,
        configuration_name='log_retention_days',
        value=_LOG_RETENTION_DAYS)
    logging.debug("[{}] Set log_retention_days to: {}".format(resource_id, _LOG_RETENTION_DAYS))

_LOG_RETENTION_DAYS = "7"
