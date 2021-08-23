import re
import logging

_PATTERN = re.compile('^//compute.googleapis.com/projects/([^/]*)/zones/([^/]*)/instances/([^/]*)$', re.IGNORECASE)
_METADATA_KEY = 'block-project-ssh-keys'
# Force setting block-project-ssh-keys, regardless of the current setting
_FORCE = True


def run(ctx):
    m = _PATTERN.match(ctx.resource_id)
    if not m:
        raise ValueError("Invalid resource_id: {}".format(ctx.resource_id))
    project_name = m.group(1)
    zone_name = m.group(2)
    instance_id = m.group(3)
    log_prefix = "[{}/{}/{}] ".format(project_name, zone_name, instance_id)

    client = ctx.get_client().get('compute', 'v1')
    logging.debug(log_prefix + "Looking up instance")
    instance = client.instances().get(project=project_name, zone=zone_name, instance=instance_id).execute()
    instance_metadata = instance.get("metadata")
    if not _FORCE and _is_metadata_set(instance_metadata):
        logging.info(log_prefix + _METADATA_KEY + " already set")
        return
    logging.info(log_prefix + "Setting " + _METADATA_KEY)
    client.instances().setMetadata(project=project_name, zone=zone_name, instance=instance_id,
                                   body=instance_metadata).execute()


def _is_metadata_set(metadata):
    if not metadata:
        return False
    metadata_items = metadata.get('items')
    if not metadata_items:
        return False
    for metadata_item in metadata_items:
        if not metadata_item:
            continue
        if metadata_item.get('key') != _METADATA_KEY:
            continue
        if metadata_item.get('value') == 'true':
            return True
    return False
