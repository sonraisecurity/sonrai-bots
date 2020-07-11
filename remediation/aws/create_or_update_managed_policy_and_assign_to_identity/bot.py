import sonrai.platform.aws.arn

import botocore
import json


def run(ctx):
    # Get policy from config
    config = ctx.config
    data = config.get_unstructured_data()
    policy_to_apply = None
    if "policy" in data:
        policy_to_apply = json.dumps(data['policy'])

    # Get role name
    resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    policy_arn = ctx.resource_id
    policy_name = resource_arn \
        .assert_service("iam") \
        .assert_type("policy") \
        .resource

    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    # Update policy or create
    try:
        policy = iam_client.get_policy(PolicyArn=policy_arn)

        version_list = iam_client.list_policy_versions(PolicyArn=policy_arn)['Versions']
        if len(version_list) == 5:
            iam_client.delete_policy_version(PolicyArn=policy_arn, VersionId=version_list[4]['VersionId'])

        iam_client.create_policy_version(PolicyArn=policy_arn, PolicyDocument=policy_to_apply, SetAsDefault=True)
    except botocore.exceptions.ClientError as error:
        iam_client.create_policy(PolicyName=policy_name, PolicyDocument=policy_to_apply)

    # Attach to identity
    identity = sonrai.platform.aws.arn.parse(data['identity'])

    if identity.resource_type == 'user':
        iam_client.attach_user_policy(UserName=identity.resource, PolicyArn=policy_arn)
    elif identity.resource_type == 'group':
        iam_client.attach_group_policy(GroupName=identity.resource, PolicyArn=policy_arn)
    elif identity.resource_type == 'role':
        iam_client.attach_role_policy(RoleName=identity.resource, PolicyArn=policy_arn)
    else:
        raise Exception('Expected identity to be of resource type (user/role/group)')

