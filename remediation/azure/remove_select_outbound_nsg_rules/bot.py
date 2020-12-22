import logging
import copy

from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.v2020_06_01.models import NetworkSecurityGroup
from azure.mgmt.network.v2020_06_01.models import SecurityRule
from sonrai.platform.azure.resource import ParsedResourceId


def run(ctx):
    object_id = ctx.resource_id

    resource_id = ParsedResourceId(object_id)

    client = ctx.get_client()
    network_client = NetworkManagementClient(client.credential, resource_id.subscription)

    direction = 'Outbound' #'Inbound'
    ports_protocols = ['80/tcp','443/tcp','22/*','3389/*'] #None

    try:
        
        nsg = network_client.network_security_groups.get(resource_group_name=resource_id.resourcegroup, network_security_group_name=resource_id.name)
        
        logging.info('retrieved network security group: {}'.format(nsg.id))

        # Find and remove any matching Allow rules
        rules_to_keep = []
        for sr in nsg.security_rules:
          rules = check_rule(sr, direction, ports_protocols)
          if rules is None:
            logging.info('Removing rule: {}'.format(sr.name))
          else:
            rules_to_keep = rules_to_keep + rules

        nsg.security_rules = rules_to_keep

        result = network_client.network_security_groups.begin_create_or_update(resource_group_name=resource_id.resourcegroup, network_security_group_name=resource_id.name, parameters=nsg).result()

        logging.info('Update complete - Status: {}'.format(result.provisioning_state))

    except Exception as e:
      raise e

def check_rule(rule, direction, ports_protocols):
    # Deny or wrong direction so just return it
    if rule.access != 'Allow' or rule.direction != direction:
      return [rule]

    # If no ports or protocols then skip, as we want to remove all
    if ports_protocols is None or len(ports_protocols) < 1:
      return None
    
    if (direction == 'Inbound'):
      test_port_range = rule.destination_port_range
    else:
      test_port_range = rule.source_port_range

    ports = (test_port_range if test_port_range != '*' else '0-65535').split('-')
    min_rule_port = int(ports[0])
    max_rule_port = int(ports[1]) if len(ports) > 1 else min_rule_port

    # Check against protocols and ports
    for pp in ports_protocols:
      pp_split = pp.split('/')
      protocol = pp_split[1]

      # protocols don't match or overlap so skip
      if (protocol != rule.protocol and protocol != '*' and rule.protocol != '*'):
        continue

      port = pp_split[0]
      ports = (port if port != '*' else '0-65535').split('-')
      min_port = int(ports[0])
      max_port = int(ports[1]) if len(ports) > 1 else min_port

      # if outside of port range continue
      if min_port > max_rule_port or max_port < min_rule_port:
        continue

      # Full overlap remove it (already checked protocols above)
      if min_port <= min_rule_port and max_port >= max_rule_port:
        return None

      # There is port overlap so we have to split the rule
      rule2 = copy.copy(rule)
      
      org_name = rule.name
      if (direction == 'Inbound'):
        rule.destination_port_range = str(min_rule_port) + '-' + str((min_port - 1))
        rule2.destination_port_range = str((max_port + 1)) + '-' + str(max_rule_port)
        rule2.priority = rule.priority + 1
      else:
        rule.source_port_range = str(min_rule_port) + '-' + str((min_port - 1))
        rule2.source_port_range = str((max_port + 1)) + '-' + str(max_rule_port)
        rule2.priority = rule.priority + 1

      rule.name = org_name + '-A'
      rule2.name = org_name + '-B'

      logging.info("Split rule {}, into {} and {}".format(org_name, rule.name, rule2.name))
      return [rule, rule2]

    return [rule]
        
