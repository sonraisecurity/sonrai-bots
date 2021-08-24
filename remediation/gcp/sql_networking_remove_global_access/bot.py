import logging
import re

_PATTERN = re.compile('^//sqladmin.googleapis.com/projects/([^/]+)/instances/([^/]+)$', re.IGNORECASE)


def run(ctx):
    m = _PATTERN.match(ctx.resource_id)
    if not m:
        raise ValueError("Invalid resource_id: {}".format(ctx.resource_id))
    project_name = m.group(1)
    instance_id = m.group(2)
    client_kwargs = {
        "project": project_name,
        "instance": instance_id
    }
    log_prefix = "[{}] ".format(client_kwargs)
    client = ctx.get_client().get('sqladmin', 'v1')
    logging.debug(log_prefix + "Looking up instance")
    instance = client.instances().get(**client_kwargs).execute()
    settings = instance.get("settings")
    if not settings:
        logging.info(log_prefix + "No 'settings'. Nothing to do")
        return
    ip_configuration = settings.get("ipConfiguration")
    if not ip_configuration:
        logging.info(log_prefix + "No 'settings.ipConfiguration'. Nothing to do")
        return
    authorized_networks = ip_configuration.get("authorizedNetworks")
    if not authorized_networks:
        logging.info(log_prefix + "No 'settings.ipConfiguration.authorizedNetworks'. Nothing to do")
        return
    # Remove any 0.0.0.0/0
    original_len = len(authorized_networks)
    authorized_networks[:] = [
        authorized_network for authorized_network in authorized_networks
        if (not _is_global(authorized_network))
    ]
    removed = original_len - len(authorized_networks)
    if not removed:
        logging.info("No 0.0.0.0/0 entries found in 'settings.ipConfiguration.authorizedNetworks'. Nothing to do")
        return
    logging.info(log_prefix + "Removed " + str(removed) + " entries. Updating")
    client.instances().patch(body=instance, **client_kwargs).execute()


def _is_global(authorized_network):
    if not authorized_network:
        return False
    value = authorized_network.get("value")
    if not value:
        return False
    value = str(value).strip()
    return value == '0.0.0.0/0'
