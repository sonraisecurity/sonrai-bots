import json
import logging
import sonrai.platform.aws.arn


def run(ctx):
    # iam
    analytic_evidence = ctx.get_analytic_evidence()
    data = analytic_evidence.get('data')
    policy_to_apply = None
    if "policy" in data:
        policy_to_apply = json.dumps(data['policy'])

    # identity
    identity = sonrai.platform.aws.arn.parse(data['resourceId'])
    policy_name = identity.resource

    client = ctx.get_client().get(identity.service)

    # Verify inline policy is to be applied with policyResourceId==NA
    if data['policyResourceId'] == 'NA':

        if identity.service == 'iam':
            if identity.resource_type == 'user':
                client.put_user_policy(UserName=identity.resource, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity.resource_type == 'group':
                client.put_group_policy(GroupName=identity.resource, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity.resource_type == 'role':
                client.put_role_policy(RoleName=identity.resource, PolicyName=policy_name, PolicyDocument=policy_to_apply)
        elif identity.service == 'kms':
            client.put_key_policy(KeyId=identity.resource, PolicyName=policy_name, PolicyDocument=policy_to_apply)
        elif identity.service == 's3':
            client.put_bucket_policy(Bucket=identity.resource,ConfirmRemoveSelfBucketAccess=True, Policy=policy_to_apply)
        else:
            logging.error('service of type {} is not supported for inline policy remediation'.format(identity.resource))