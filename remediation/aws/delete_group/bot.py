import logging
import sonrai.platform.aws.arn

log = logging.getLogger()

def _iter_responses(f, *args, **kwargs):
    while True:
        response = f(*args, **kwargs)
        yield response
        if not response["IsTruncated"]:
            return
        marker = response["Marker"]
        if not marker:
            return
        kwargs["Marker"] = marker

def run(ctx):
    client = ctx.get_client().get('iam')
    group_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    group_name = group_arn \
        .assert_service("iam") \
        .assert_type("group") \
        .name
    # Detach all group managed policies
    for response in _iter_responses(client.list_attached_group_policies, GroupName=group_name):
        for policy in response["AttachedPolicies"]:
            policy_arn = policy["PolicyArn"]
            log.info("[{}] Detaching group managed policy: {}".format(group_arn, policy_arn))
            client.detach_group_policy(GroupName=group_name, PolicyArn=policy_arn)
    # Delete all group inline policies
    for response in _iter_responses(client.list_group_policies, GroupName=group_name):
        for policy_name in response["PolicyNames"]:
            log.info("[{}] Deleting group inline policy: {}".format(group_arn, policy_name))
            client.delete_group_policy(GroupName=group_name, PolicyName=policy_name)
    # Remove all users from the group
    for response in _iter_responses(client.get_group, GroupName=group_name):
        for user in response["Users"]:
            user_name = user["UserName"]
            log.info("[{}] Removing user from group: {}".format(group_arn, user_name))
            client.remove_user_from_group(GroupName=group_name, UserName=user_name)

    log.info("[{}] Deleting group".format(group_arn))
    client.delete_group(GroupName=group_name)
    log.info("[{}] Group deleted".format(group_arn))
