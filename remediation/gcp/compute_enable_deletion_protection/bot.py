import re
import logging
import googleapiclient.errors

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
    logging.debug(log_prefix + "Looking up instance")
    instance = client.instances().get(**client_kwargs).execute()
    if instance.get("deletionProtection") is True:
        logging.info(log_prefix + "deletionProtection is true, nothing to do")
        return
    instance["deletionProtection"] = True
    logging.info(log_prefix + "Setting deletionProtection to true and updating instance")
    try:
        client.instances().update(body=instance, **client_kwargs).execute()
    except googleapiclient.errors.HttpError as e:
        # In order to populate error_details, __repr__ must be called
        repr(e)
        error_details = getattr(e, "error_details", "")
        # If another operation was in progress, wait
        if error_details and "instance attached to Managed Instance Group" in error_details:
            logging.info(log_prefix + "Instance is attached to a Managed Instance Group. "
                                      "Can not update deletion protection")
            return
        raise
