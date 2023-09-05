import sonrai.platform.aws.arn

import logging

def run(ctx):
    # Create AWS CloudFormation client
    cf_client = ctx.get_client().get('cloudformation')

    stack_resource_srn = ctx.resource_srn

    stack_name = stack_resource_srn.split('/')[-2]

    logging.info(f'Deleting stack {stack_name}.')
    cf_client.delete_stack(StackName=stack_name)
