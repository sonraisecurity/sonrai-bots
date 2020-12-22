import logging

import sonrai.platform.aws.arn

def run(ctx):
    resource_id = ctx.resource_id
    resource_arn = sonrai.platform.aws.arn.parse(resource_id)
    vpcid = resource_arn \
        .assert_service("ec2") \
        .assert_type("vpc") \
        .resource
    logging.info('Removing VPC ({}) from AWS'.format(vpcid))
    ec2client = ctx.get_client().get('ec2')
    response = ec2client.delete_vpc(VpcId=vpcid)
    logging.info('Removed VPC: {}'.format(response))