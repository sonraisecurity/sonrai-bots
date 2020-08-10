import sonrai.platform.aws.arn

import botocore
import json
import logging


def run(ctx):
    # Get data for bot from ctx
    data_enum = ctx.get_policy_evidence_data()

    # loop for each analytic data result
    for data in data_enum:

        policy_to_apply = None
        if "policy" in data:
            policy_to_apply = json.dumps(data['policy'])

        # Verify inline policy is to be applied with policyResourceId==NA
        if data['policyResourceId'] == 'NA':

            # identity
            identity = sonrai.platform.aws.arn.parse(data['resourceId'])
            policy_name = identity.name

            client = ctx.get_client().get(identity.service)

            if identity.service == 'iam':
                if identity.resource_type == 'user':
                    client.put_user_policy(UserName=identity.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
                elif identity.resource_type == 'group':
                    client.put_group_policy(GroupName=identity.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
                elif identity.resource_type == 'role':
                    client.put_role_policy(RoleName=identity.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity.service == 'kms':
                client.put_key_policy(KeyId=identity.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity.service == 's3':
                client.put_bucket_policy(Bucket=identity.name, ConfirmRemoveSelfBucketAccess=True, Policy=policy_to_apply)
            else:
                raise Exception('service of type {} is not supported for inline policy remediation'.format(identity.service))

        else:

            # Attach to identity
            identity_arn = data['resourceId']
            identity = sonrai.platform.aws.arn.parse(data['resourceId'])

            # Get role name
            resource_arn = sonrai.platform.aws.arn.parse(data['policyResourceId'])
            policy_arn = data['policyResourceId']
            policy_name = resource_arn \
                .assert_service("iam") \
                .assert_type("policy") \
                .name

            logging.info('Creating or updating policy: {} and attaching to identity: {}'.format(policy_arn, identity_arn))

            # Create AWS identity and access management client
            iam_client = ctx.get_client().get('iam')

            # Create or update policy
            policy_arn = create_or_update_policy(iam_client=iam_client, policy_arn=policy_arn, policy_name=policy_name, policy_to_apply=policy_to_apply, identity=identity, resource_arn=resource_arn)

            # Attach to identity
            if identity.resource_type == 'user':
                iam_client.attach_user_policy(UserName=identity.name, PolicyArn=policy_arn)
            elif identity.resource_type == 'group':
                iam_client.attach_group_policy(GroupName=identity.name, PolicyArn=policy_arn)
            elif identity.resource_type == 'role':
                iam_client.attach_role_policy(RoleName=identity.name, PolicyArn=policy_arn)
            else:
                raise Exception('Expected identity to be of resource type (user/role/group)')


def create_or_update_policy(iam_client=None, policy_arn=None, policy_name=None, policy_to_apply=None, identity=None, resource_arn=None):
    try:
        policy = iam_client.get_policy(PolicyArn=policy_arn)

        version_list = iam_client.list_policy_versions(PolicyArn=policy_arn)['Versions']
        if len(version_list) == 5:
            iam_client.delete_policy_version(PolicyArn=policy_arn, VersionId=version_list[4]['VersionId'])

        iam_client.create_policy_version(PolicyArn=policy_arn, PolicyDocument=policy_to_apply, SetAsDefault=True)
        return policy_arn
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchEntity':
            iam_client.create_policy(PolicyName=policy_name, PolicyDocument=policy_to_apply)
            return policy_arn
        elif error.response['Error']['Code'] == 'AccessDenied':
            # Detach policy
            try:
                if identity.resource_type == 'user':
                    iam_client.detach_user_policy(UserName=identity.name, PolicyArn=policy_arn)
                elif identity.resource_type == 'group':
                    iam_client.detach_group_policy(GroupName=identity.name, PolicyArn=policy_arn)
                elif identity.resource_type == 'role':
                    iam_client.detach_role_policy(RoleName=identity.name, PolicyArn=policy_arn)
            except Exception as error:
                logging.error('{}'.format(error))

            # Remane AWS Managed policy
            policy_name = policy_name + 'SonraiManaged'
            policy_arn = 'arn:{}:{}:{}:{}:{}/{}'.format(resource_arn.partition,resource_arn.service,resource_arn.region,identity.account_id,resource_arn.resource_type, policy_name).replace('None', '')
            return create_or_update_policy(iam_client=iam_client, policy_arn=policy_arn, policy_name=policy_name, policy_to_apply=policy_to_apply)



