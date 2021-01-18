import logging
import sonrai.platform.aws.arn

log = logging.getLogger()

# Remove inbound role from a security group : AWS ref(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.revoke_security_group_ingress)

def run(ctx):

  # Setp 1) Get resource id from ticket data
  resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)

  # Step 2) Get EC2 instance id from resource id
  instance_id = resource_arn \
    .assert_service("ec2") \
    .assert_type("instance") \
    .name

  # Step 3) Get region from resource id
  region = resource_arn \
    .assert_service("ec2") \
    .assert_type("instance") \
    .region

  # Step 4) Get AWS Client for EC2 service
  client = ctx.get_client().get('ec2', region)

  # Step 5) Get security group details from EC2 instance and remove all inbound port/protocol from security group
  ec2_response = client.describe_instances(InstanceIds=[instance_id])
  for reservations in ec2_response['Reservations']:
    for instance in reservations['Instances']:
      for security_group in instance['SecurityGroups']:
        security_group_id = security_group['GroupId']
        security_group_response = client.describe_security_groups(GroupIds=[security_group_id])
        for security_group_detail in security_group_response['SecurityGroups']:
          ip_permissions = security_group_detail['IpPermissions']
          if(len(ip_permissions)==0):
            log.warning("[{}] No inbound port/protocol to remove from security group".format(security_group_id))
          else:
            log.info("[{}] Removing all inbound port/protocol from security group".format(security_group_id))
            client.revoke_security_group_ingress(GroupId=security_group_id, IpPermissions=ip_permissions)
            log.info("[{}] Removed all inbound port/protocol from security group".format(security_group_id))
