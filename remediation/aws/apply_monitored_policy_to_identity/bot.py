import sonrai.platform.aws.arn
import sonrai.platform.srn

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
        if not data:
            continue
        _apply(ctx, data)


def _apply(ctx, data):
    policy_document = data.get("monitoredActionsPolicy", None)
    if policy_document:
        policy_document = policy_document.as_plain_ordered_dict()
    policy_type = policy_document.get("type", "attach")
    if policy_type == 'detach':
        policy_document = None
    else:
        # Sanitize
        policy_document.pop("message", None)
        policy_document.pop("type", None)

    identity_arn = sonrai.platform.aws.arn.parse(data['resourceId'])
    policy_document_str = json.dumps(policy_document) if policy_document else None

    # Verify inline policy_document is to be applied with policyResourceId==NA
    if data['policyResourceId'] == 'NA':
        iam_client = ctx.get_client().get(identity_arn.service)
        policy_name = data['policySrn'].split("/")[len(data['policySrn'].split("/")) - 1]
        if policy_document:
            put_inline_policy(iam_client, identity_arn, policy_name, policy_document_str)
        else:
            delete_inline_policy(iam_client, identity_arn, policy_name)
    else:
        iam_client = ctx.get_client().get('iam')
        policy_arn = sonrai.platform.aws.arn.parse(data['policyResourceId']) \
            .assert_service("iam") \
            .assert_type("policy")
        # Detach existing policy
        detach_policy(iam_client, policy_arn, identity_arn)
        # If policy was specified, create and attach
        if policy_document:
            # Create or update policy
            policy_arn = create_policy(iam_client, policy_arn, policy_document_str)
            # Attach new policy
            attach_policy(iam_client, policy_arn, identity_arn)


def delete_inline_policy(iam_client, identity_arn, policy_name):
    logging.info('[{}] Deleting inline policy from identity: {}'.format(policy_name, identity_arn))
    try:
        if identity_arn.service == 'iam':
            if identity_arn.resource_type == 'user':
                iam_client.delete_user_policy(UserName=identity_arn.name, PolicyName=policy_name)
            elif identity_arn.resource_type == 'group':
                iam_client.delete_group_policy(GroupName=identity_arn.name, PolicyName=policy_name)
            elif identity_arn.resource_type == 'role':
                iam_client.delete_role_policy(RoleName=identity_arn.name, PolicyName=policy_name)
            else:
                raise Exception('Expected identity to be of resource type (user/role/group): {}'.format(identity_arn))
        # TODO Deleting an inline policy for KMS would cause it to no longer be manageable
        # elif identity_arn.service == 'kms':
        #    iam_client.delete_key_policy(KeyId=identity_arn.name, PolicyName=policy_name)
        elif identity_arn.service == 's3':
            iam_client.delete_bucket_policy(Bucket=identity_arn.name, ConfirmRemoveSelfBucketAccess=True)
        else:
            raise Exception("identity is not supported for inline policy remediation: {}".format(identity_arn))
    except botocore.exceptions.ClientError as error:
        if not error.response['Error']['Code'] == 'NoSuchEntity':
            raise
        logging.info('[{}] Inline policy already deleted from identity: {}'.format(policy_name, identity_arn))


def put_inline_policy(iam_client, identity_arn, policy_name, policy_document_str):
    logging.info('[{}] Creating inline policy for identity: {}'.format(policy_name, identity_arn))
    if identity_arn.service == 'iam':
        if identity_arn.resource_type == 'user':
            iam_client.put_user_policy(UserName=identity_arn.name, PolicyName=policy_name,
                                       PolicyDocument=policy_document_str)
        elif identity_arn.resource_type == 'group':
            iam_client.put_group_policy(GroupName=identity_arn.name, PolicyName=policy_name,
                                        PolicyDocument=policy_document_str)
        elif identity_arn.resource_type == 'role':
            iam_client.put_role_policy(RoleName=identity_arn.name, PolicyName=policy_name,
                                       PolicyDocument=policy_document_str)
        else:
            raise Exception('Expected identity to be of resource type (user/role/group): {}'.format(identity_arn))
    elif identity_arn.service == 'kms':
        iam_client.put_key_policy(KeyId=identity_arn.name, PolicyName=policy_name,
                                  PolicyDocument=policy_document_str)
    elif identity_arn.service == 's3':
        iam_client.put_bucket_policy(Bucket=identity_arn.name, ConfirmRemoveSelfBucketAccess=True,
                                     Policy=policy_document_str)
    else:
        raise Exception("identity is not supported for inline policy remediation: {}".format(identity_arn))


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


def create_policy(iam_client, policy_arn, policy_document_str):
    policy_arn = _new_policy_arn(policy_arn, policy_document_str)
    logging.info("New policy: {}".format(policy_arn))
    logging.info("[{}] Creating policy".format(policy_arn))
    try:
        iam_client.create_policy(PolicyName=policy_arn.name, PolicyDocument=policy_document_str)
    except botocore.exceptions.ClientError as error:
        if not error.response['Error']['Code'] == 'EntityAlreadyExists':
            raise
        logging.info("[{}] Policy already exists".format(policy_arn))
    return policy_arn


def _new_policy_arn(policy_arn, policy_document_str):
    policy_name = policy_arn.name
    m = _SONRAI_POLICY_NAME_PATTERN.match(policy_name)
    if m:
        base = m.group(1)
    else:
        base = "Sonrai-" + policy_name
    policy_name = base + "-" + hashlib.md5(policy_document_str.encode('utf-8')).hexdigest()
    return sonrai.platform.aws.arn.parse('arn:{}:{}:{}:{}:{}/{}'.format(
        policy_arn.partition or '', policy_arn.service or '', policy_arn.region or '',
        policy_arn.account_id or '', policy_arn.resource_type or '', policy_name))


_SONRAI_POLICY_NAME_PATTERN = re.compile("^(Sonrai-.+)-[^-]+$")


_POLICY_MAX_SIZE = 6144
_SONRAI_POLICY_NAME_PATTERN = re.compile("^(Sonrai-.+)-[^-]+$")
