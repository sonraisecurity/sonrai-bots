import logging

import sonrai.platform.aws.arn

def run(ctx):
    arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    vpcid = arn \
        .assert_service("ec2") \
        .assert_type("vpc") \
        .resource
    logging.info('Removing VPC ({}) from AWS'.format(vpcid))
    ec2client = ctx.get_client().get('ec2', region=arn.region)
    response = ec2client.delete_vpc(VpcId=vpcid)
    logging.info('Removed VPC: {}'.format(response))