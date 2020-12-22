import logging
import sonrai.platform.aws.arn


def run(ctx):


    # Parse resource id to group
    resource_id = ctx.resource_id
    resource_arn = sonrai.platform.aws.arn.parse(resource_id)
    group_id = resource_arn \
        .assert_service("ec2") \
        .assert_type("security-group") \
        .resource

    # Create AWS EC2 client
    ec2_client = ctx.get_client().get('ec2', region=resource_arn.region)

    # Refers doc https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DeleteSecurityGroup.html
    response = ec2_client.delete_security_group(GroupId=group_id,)
    logging.info('deleted security group: {}'.format(response))

