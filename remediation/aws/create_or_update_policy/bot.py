import logging

import sonrai.platform.aws.arn
import json


def run(ctx):
    # Get policy from config
    config = ctx.config
    data = ctx.get_analytic_evidence()
    policy_to_apply = None
    if "policy" in data:
        policy_to_apply = json.dumps(data['policy'])

    # Get role name
    resource_arn = sonrai.platform.aws.arn.parse(data['policyResourceId'])
    policy_arn = data['policyResourceId']
    resource_arn \
    .assert_service("iam") \
    .assert_type("policy") \
    .resource

    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    # https://stackoverflow.com/questions/50935599/how-to-update-iam-policy-using-boto3-python
    policy = iam_client.get_policy(PolicyArn=policy_arn)

    version_list = iam_client.list_policy_versions(PolicyArn=policy_arn)['Versions']
    if len(version_list) == 5:
        iam_client.delete_policy_version(PolicyArn=policy_arn, VersionId=version_list[4]['VersionId'])


    logging.info('Updating policy: {}'.format(policy_arn))
    iam_client.create_policy_version(PolicyArn=policy_arn, PolicyDocument=policy_to_apply, SetAsDefault=True)