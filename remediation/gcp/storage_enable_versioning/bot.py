import re
import logging

_PATTERN = re.compile('^//storage\.googleapis\.com/projects/([^/]+)/buckets/(.+)$', re.IGNORECASE)
# Force updates, regardless of the current setting
_FORCE = True


def run(ctx):
    m = _PATTERN.match(ctx.resource_id)
    if not m:
        raise ValueError("Invalid resource_id: {}".format(ctx.resource_id))
    bucket_name = m.group(2)
    client_kwargs = {
        "bucket": bucket_name,
    }
    log_prefix = "[{}] ".format(client_kwargs)

    # GCP does not allow updating enableFlowLogs and logConfig in the same call
    # Set enableFlowLogs first, then set the logConfig
    client = ctx.get_client().get('storage', 'v1')

    # Initialize values based on any existing logConfig
    logging.debug(log_prefix + "Looking up bucket")
    req = client.buckets().get(**client_kwargs)
    bucket = req.execute()
    versioning = bucket.get("versioning")
    if not versioning:
        versioning = {}
        bucket["versioning"] = versioning
    if not _FORCE and versioning.get("enabled") is not True:
        logging.info(log_prefix + "versioning.enabled already set")
        return
    versioning["enabled"] = True
    logging.info(log_prefix + "Setting versioning.enabled")
    client.buckets().patch(body=bucket, **client_kwargs).execute()


