import logging

import sonrai.platform.aws.arn
import json


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
            policy_name = "Sonrai-"identity.name

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