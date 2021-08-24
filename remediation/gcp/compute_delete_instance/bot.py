import re
import logging

_PATTERN = re.compile('^//compute.googleapis.com/projects/([^/]+)/zones/([^/]+)/instances/([^/]+)$', re.IGNORECASE)


def run(ctx):
    m = _PATTERN.match(ctx.resource_id)
    if not m:
        raise ValueError("Invalid resource_id: {}".format(ctx.resource_id))
    project_name = m.group(1)
    zone_name = m.group(2)
    instance_id = m.group(3)
    client_kwargs = {
        "project": project_name,
        "zone": zone_name,
        "instance": instance_id
    }
    log_prefix = "[{}] ".format(client_kwargs)
    # Lookup instance metadata
    client = ctx.get_client().get('compute', 'v1')
    logging.info(log_prefix + "Deleting instance")
    client.instances().delete(**client_kwargs).execute()
