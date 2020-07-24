import botocore
import logging
import sonrai.platform.aws.arn


def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    resource_id = ctx.resource_id
    resource_arn = sonrai.platform.aws.arn.parse(resource_id)
    user_name = resource_arn \
        .assert_service("iam") \
        .assert_type("user") \
        .resource

    # Delete the user AWS ref(https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_manage.html#id_users_deleting_cli)

    # Step 1)
    try:
        iam_client.delete_login_profile(UserName=user_name, )
    except botocore.exceptions.ClientError as error:
        # Just because the user doesnt have a login profile doesnt mean the user doesnt exist
        pass

    # Step 2)
    access_key_list = iam_client.list_access_keys(UserName=user_name, )
    for accessKey in access_key_list['AccessKeyMetadata']:
        iam_client.delete_access_key(UserName=user_name, AccessKeyId=accessKey['AccessKeyId'])

    # Step 3)
    signing_certificate_list = iam_client.list_signing_certificates(UserName=user_name, )
    for certificate in signing_certificate_list['Certificates']:
        iam_client.delete_signing_certificate(UserName=user_name, CertificateId=certificate['CertificateId'])

    # Step 4)
    ssh_key_list = iam_client.list_ssh_public_keys(UserName=user_name, )
    for ssh_key in ssh_key_list['SSHPublicKeys']:
        iam_client.delete_ssh_public_key(UserName=user_name, SSHPublicKeyId=ssh_key['SSHPublicKeyId'])

    # Step 5)
    service_specific_credential_list = iam_client.list_service_specific_credentials(UserName=user_name, )
    for service_specific_credential in service_specific_credential_list['ServiceSpecificCredentials']:
        iam_client.delete_service_specific_credential(UserName=user_name,
                                                      ServiceSpecificCredentialId=service_specific_credential[
                                                          'ServiceSpecificCredentialId'])

    # Step 6)
    mfa_list = iam_client.list_mfa_devices(UserName=user_name, )
    for mfa in mfa_list['MFADevices']:
        iam_client.deactivate_mfa_device(UserName=user_name, SerialNumber=mfa['SerialNumber'])
        iam_client.delete_virtual_mfa_device(SerialNumber=mfa['SerialNumber'])

    # Step 7)
    user_policy_list = iam_client.list_user_policies(UserName=user_name, )
    for user_policy_name in user_policy_list['PolicyNames']:
        iam_client.delete_user_policy(UserName=user_name, PolicyName=user_policy_name)

    # Step 8)
    attached_user_policy_list = iam_client.list_attached_user_policies(UserName=user_name, )
    for attached_policy in attached_user_policy_list['AttachedPolicies']:
        iam_client.detach_user_policy(UserName=user_name, PolicyArn=attached_policy['PolicyArn'])

    # Step 9)
    user_group_list = iam_client.list_groups_for_user(UserName=user_name, )
    for group in user_group_list['Groups']:
        iam_client.remove_user_from_group(GroupName=group['GroupName'], UserName=user_name)

    # Step 10)
    logging.info('deleted user: {}'.format(resource_id))
    iam_client.delete_user(UserName=user_name)
