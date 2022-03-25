import re
import logging

_PATTERN = re.compile('^//compute\.googleapis\.com/projects/([^/]+)/zones/([^/]+)/instances/([^/]+)$', re.IGNORECASE)
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
    # Lookup instance metadata
    client = ctx.get_client().get('compute', 'v1')
    logging.debug(log_prefix + "Looking up instance")
    instance = client.instances().get(project=project_name, zone=zone_name, instance=instance_id).execute()
    instance_metadata = instance.get("metadata")
    logging.info(log_prefix + "Setting " + _METADATA_KEY)
    # Set block-project-ssh-keys
    if _set_block_project_wide_ssh_keys(instance_metadata) and not _FORCE:
        # If the key was already set, and we are not forcing an update
        logging.info(log_prefix + _METADATA_KEY + " already set")
        return
    # Update the instance metadata
    logging.info(log_prefix + "Updating metadata")
    client.instances().setMetadata(project=project_name, zone=zone_name, instance=instance_id,
                                   body=instance_metadata).execute()


def _set_block_project_wide_ssh_keys(metadata):
    if "items" not in metadata:
        metadata["items"] = []
    metadata_items = metadata["items"]
    for metadata_item in metadata_items:
        if not metadata_item:
            continue
        if metadata_item.get('key') != _METADATA_KEY:
            continue
        if metadata_item.get('value') == 'true':
            return True
        else:
            metadata_item['value'] = 'true'
            return False
    metadata_items.append({
        'key': _METADATA_KEY,
        'value': 'true'
    })
    return False
