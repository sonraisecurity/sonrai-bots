import logging

import sonrai.platform.aws.arn
import json


def run(ctx):
    # Get policy from config
    config = ctx.config
    data = ctx.get_analytic_evidence()
    policy = None
    if "policy" in data:
        policy = json.dumps(data['policy'])

    # Get role name
    resource_arn = sonrai.platform.aws.arn.parse(data['resourceId'])
    role_name = resource_arn \
        .assert_service("iam") \
        .assert_type("role") \
        .name

    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    # Update trust policy
    logging.info('Update trust policy on role: {}'.format(data['resourceId']))
    iam_client.update_assume_role_policy(RoleName=role_name, PolicyDocument=policy)
