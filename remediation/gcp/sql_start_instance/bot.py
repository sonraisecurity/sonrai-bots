import logging
import re
import time
import googleapiclient.errors

_PATTERN = re.compile('^//sqladmin.googleapis.com/projects/([^/]+)/instances/([^/]+)$', re.IGNORECASE)
# If an existing operation is in progress, how long to wait before re-attempting
_POLL_SEC = 30
# If an existing operation is in progress, how many times to re-attempt
_MAX_ATTEMPTS = 10


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
    attempts = 0
    while attempts < _MAX_ATTEMPTS:
        attempts = attempts + 1
        logging.debug(log_prefix + "Looking up instance")
        instance = client.instances().get(**client_kwargs).execute()
        settings = instance.get("settings")
        if not settings:
            settings = {}
            instance["settings"] = settings
        if settings.get("activationPolicy") == "ALWAYS":
            logging.info(log_prefix + "settings.activationPolicy is 'ALWAYS'. Nothing to do")
            return
        settings["activationPolicy"] = "ALWAYS"
        logging.info(log_prefix + "Starting instance")
        try:
            client.instances().patch(body=instance, **client_kwargs).execute()
        except googleapiclient.errors.HttpError as e:
            # In order to populate error_details, __repr__ must be called
            repr(e)
            error_details = getattr(e, "error_details", "")
            # If another operation was in progress, wait
            if error_details and "another operation was already in progress" in error_details:
                logging.info(log_prefix + "Another operation was in progress. Waiting " + str(_POLL_SEC) + "sec")
                time.sleep(_POLL_SEC)
                continue
            raise
        else:
            return
    raise ValueError("Timed out after {} attempts".format(_MAX_ATTEMPTS))
