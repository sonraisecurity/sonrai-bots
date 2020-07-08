import sonrai.aws
import json


def run(ctx):
    # Get policy from config
    config = ctx.config
    data = config.get_unstructured_data()
    policy = None
    if "policy" in data:
        policy = json.dumps(data['policy'])

    # Get role name
    resource_arn = sonrai.aws.parse_arn(ctx.resource_id)
    role_name = resource_arn \
        .assert_service("iam") \
        .assert_type("role") \
        .resource

    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    # Update trust policy
    iam_client.update_assume_role_policy(RoleName=role_name, PolicyDocument=policy)
