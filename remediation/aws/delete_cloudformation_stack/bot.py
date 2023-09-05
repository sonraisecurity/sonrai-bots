import sonrai.platform.aws.arn

import logging

def run(ctx):
    arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    stack_name = arn \
        .assert_service('cloudformation') \
        .assert_type('stack') \
        .resource \
        .split('/')[-2]

    # Create AWS CloudFormation client
    cf_client = ctx.get_client().get('cloudformation', region=arn.region)

    logging.info(f'Deleting stack {stack_name} in region {arn.region}')
    cf_client.delete_stack(StackName=stack_name)
