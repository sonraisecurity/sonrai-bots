import re
import logging

_PATTERN = re.compile('^//compute\.googleapis\.com/projects/([^/]+)/regions/([^/]+)/subnetworks/([^/]+)$', re.IGNORECASE)
_DEFAULT_FLOW_SAMPLING = 0.5
_DEFAULT_AGGREGATION_INTERVAL = 'INTERVAL_5_MIN'
# Force updates, regardless of whether or not flow logs are enabled
# Note that original logConfig values are preserved with the exception of logConfig.enable
_FORCE = True


def run(ctx):
    m = _PATTERN.match(ctx.resource_id)
    if not m:
        raise ValueError("Invalid resource_id: {}".format(ctx.resource_id))
    project_name = m.group(1)
    region_name = m.group(2)
    subnetwork_id = m.group(3)
    client_kwargs = {
        "project": project_name,
        "region": region_name,
        "subnetwork": subnetwork_id
    }
    log_prefix = "[{}] ".format(client_kwargs)

    # GCP does not allow updating enableFlowLogs and logConfig in the same call
    # Set enableFlowLogs first, then set the logConfig
    client = ctx.get_client().get('compute', 'v1')

    # Initialize values based on any existing logConfig
    logging.debug(log_prefix + "Looking up subnetwork")
    subnetwork = client.subnetworks().get(**client_kwargs).execute()
    # Initialize the logConfig based on the first lookup to save any custom settings, if any
    log_config = subnetwork.get("logConfig")
    if not log_config:
        log_config = {}

    if not _FORCE and subnetwork.get("enableFlowLogs") is True and log_config.get("enable"):
        logging.info(log_prefix + "enableFlowLogs and logConfig.enable already set")
        return

    # subnetwork.enableFlowLogs
    logging.info(log_prefix + "Updating enableFlowLogs")
    subnetwork["enableFlowLogs"] = True
    # GCP does not allow updating both at the same time, ensure no logConfig is provided
    subnetwork["logConfig"] = None
    client.subnetworks().patch(body=subnetwork, **client_kwargs).execute()
    # Re-initialize the subnetwork
    logging.debug(log_prefix + "Looking up subnetwork")
    subnetwork = client.subnetworks().get(**client_kwargs).execute()

    # subnetwork.logConfig
    log_config["enable"] = True
    if not log_config.get("flowSampling"):
        log_config["flowSampling"] = _DEFAULT_FLOW_SAMPLING
    if not log_config.get("aggregationInterval"):
        log_config["aggregationInterval"] = _DEFAULT_AGGREGATION_INTERVAL
    subnetwork["logConfig"] = log_config
    logging.info(log_prefix + "Updating logConfig")
    client.subnetworks().patch(body=subnetwork, **client_kwargs).execute()
