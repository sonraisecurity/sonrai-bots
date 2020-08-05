import logging

import sonrai.platform.aws.arn

def run(ctx):

    iam_client = ctx.get_client().get('iam')

    # Get role name
    resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    role_name = resource_arn \
        .assert_service("iam") \
        .assert_type("role") \
        .name

    # https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_manage_delete.html#roles-managingrole-deleting-api
    instance_profiles = iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for instance_profile in instance_profiles['InstanceProfiles']:
        iam_client.remove_role_from_instance_profile(InstanceProfileName=instance_profile['InstanceProfileName'], RoleName=role_name)

    role_policies = iam_client.list_role_policies(RoleName=role_name)
    for policy_name in role_policies['PolicyNames']:
        iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    role_attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    for attached_policy in role_attached_policies['AttachedPolicies']:
        iam_client.detach_role_policy(RoleName=role_name, PolicyArn=attached_policy['PolicyArn'])

    logging.info('deleting role: {}'.format(ctx.resource_id))
    iam_client.delete_role(RoleName=role_name)
