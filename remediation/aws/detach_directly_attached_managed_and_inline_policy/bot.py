import sonrai.platform.aws.arn

import logging


def run(ctx):
    # Create AWS S3 client
    iam_client = ctx.get_client().get('iam')

    user_resource_srn = ctx.resource_srn

    user_name = user_resource_srn.split('/')[-1]

    # get the list of attached managed policies
    response = iam_client.list_attached_user_policies(UserName=user_name)
    managed_policies_attached = response['AttachedPolicies']
    # detach those policies
    logging.info("Detaching all directly attached managed policies from the user {}.".format(user_name))
    for policy in managed_policies_attached:
        iam_client.detach_user_policy(UserName=user_name, PolicyArn=policy['PolicyArn'])

    # get the list of attached inline policies
    response = iam_client.list_user_policies(UserName=user_name)
    inline_policies_attached = response['PolicyNames']
    # detach those policies
    logging.info("Detaching all directly attached inline policies from the user {}.".format(user_name))
    for policy_name in inline_policies_attached:
        iam_client.delete_user_policy(UserName=user_name, PolicyName=policy_name)
