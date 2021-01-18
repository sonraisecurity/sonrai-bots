import logging
import sonrai.platform.aws.arn

log = logging.getLogger()

# Stop AWS EC2 Instance : AWS ref(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.stop_instances)

def run(ctx):

  # Setp 1) Get resource id from ticket data
  resource_id = sonrai.platform.aws.arn.parse(ctx.resource_id)

  # Step 2) Get EC2 instance id from resource id
  instance_id = resource_id \
    .assert_service("ec2") \
    .assert_type("instance") \
    .name

  # Step 3) Get region from resource id
  region = resource_id \
    .assert_service("ec2") \
    .assert_type("instance") \
    .region

  # Step 4) Get AWS Client for EC2 service
  client = ctx.get_client().get('ec2', region)

  # Step 5) Stop EC2 instance
  log.info("[{}] Stopping EC2 Instance".format(instance_id))
  client.stop_instances(InstanceIds=[instance_id])
  log.info("[{}] EC2 Instance stopped".format(instance_id))