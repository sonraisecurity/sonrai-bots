import sonrai.platform.aws.arn

import re
import botocore
import botocore.exceptions
import json
import logging
import hashlib


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
            identity_arn = sonrai.platform.aws.arn.parse(data['resourceId'])
            policy_name = data['policySrn'].split("/")[len(data['policySrn'].split("/")) - 1]

            client = ctx.get_client().get(identity_arn.service)

            if identity_arn.service == 'iam':
                if identity_arn.resource_type == 'user':
                    client.put_user_policy(UserName=identity_arn.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
                elif identity_arn.resource_type == 'group':
                    client.put_group_policy(GroupName=identity_arn.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
                elif identity_arn.resource_type == 'role':
                    client.put_role_policy(RoleName=identity_arn.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity_arn.service == 'kms':
                client.put_key_policy(KeyId=identity_arn.name, PolicyName=policy_name, PolicyDocument=policy_to_apply)
            elif identity_arn.service == 's3':
                client.put_bucket_policy(Bucket=identity_arn.name, ConfirmRemoveSelfBucketAccess=True, Policy=policy_to_apply)
            else:
                raise Exception('service of type {} is not supported for inline policy remediation'.format(identity_arn.service))

        else:

            # Attach to identity
            identity_arn = sonrai.platform.aws.arn.parse(data['resourceId'])

            # Get role name
            policy_arn = sonrai.platform.aws.arn.parse(data['policyResourceId']) \
                .assert_service("iam") \
                .assert_type("policy") \

            # Create AWS identity and access management client
            iam_client = ctx.get_client().get('iam')

            # Create or update policy
            detach_policy(iam_client, policy_arn, identity_arn)
            policy_arn = create_policy(iam_client, policy_arn, policy_to_apply)
            attach_policy(iam_client, policy_arn, identity_arn)


def detach_policy(iam_client, policy_arn, identity_arn):
    # Detach policy from the identity
    logging.info('[{}] Detaching policy from identity: {}'.format(policy_arn, identity_arn))
    try:
        if identity_arn.resource_type == 'user':
            iam_client.detach_user_policy(UserName=identity_arn.name, PolicyArn=str(policy_arn))
        elif identity_arn.resource_type == 'group':
            iam_client.detach_group_policy(GroupName=identity_arn.name, PolicyArn=str(policy_arn))
        elif identity_arn.resource_type == 'role':
            iam_client.detach_role_policy(RoleName=identity_arn.name, PolicyArn=str(policy_arn))
        else:
            raise Exception('Expected identity to be of resource type (user/role/group): {}'.format(identity_arn))
    except botocore.exceptions.ClientError as error:
        if not error.response['Error']['Code'] == 'NoSuchEntity':
            raise
        logging.info('[{}] Policy already detached from identity: {}'.format(policy_arn, identity_arn))


def attach_policy(iam_client, policy_arn, identity_arn):
    # Attach to identity
    logging.info('[{}] Attaching policy to identity: {}'.format(policy_arn, identity_arn))
    if identity_arn.resource_type == 'user':
        iam_client.attach_user_policy(UserName=identity_arn.name, PolicyArn=str(policy_arn))
    elif identity_arn.resource_type == 'group':
        iam_client.attach_group_policy(GroupName=identity_arn.name, PolicyArn=str(policy_arn))
    elif identity_arn.resource_type == 'role':
        iam_client.attach_role_policy(RoleName=identity_arn.name, PolicyArn=str(policy_arn))
    else:
        raise Exception('Expected identity to be of resource type (user/role/group): {}'.format(identity_arn))


def create_policy(iam_client, policy_arn, policy_document):
    policy_arn = _new_policy_arn(policy_arn, policy_document)
    logging.info("New policy: {}".format(policy_arn))
    logging.info("[{}] Creating policy".format(policy_arn))
    try:
        iam_client.create_policy(PolicyName=policy_arn.name, PolicyDocument=policy_document)
    except botocore.exceptions.ClientError as error:
        if not error.response['Error']['Code'] == 'EntityAlreadyExists':
            raise
        logging.info("[{}] Policy already exists".format(policy_arn))
    return policy_arn


def _new_policy_arn(policy_arn, policy_document):
    policy_name = policy_arn.name
    m = _SONRAI_POLICY_NAME_PATTERN.match(policy_name)
    if m:
        base = m.group(1)
    else:
        base = "Sonrai-" + policy_name
    policy_name = base + "-" + hashlib.md5(policy_document.encode('utf-8')).hexdigest()
    return sonrai.platform.aws.arn.parse('arn:{}:{}:{}:{}:{}/{}'.format(
        policy_arn.partition or '', policy_arn.service or '', policy_arn.region or '',
        policy_arn.account_id or '', policy_arn.resource_type or '', policy_name))


_SONRAI_POLICY_NAME_PATTERN = re.compile("^(Sonrai-.+)-[^-]+$")
