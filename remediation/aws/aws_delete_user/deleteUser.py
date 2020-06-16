import botocore


def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx['client'].get('iam')

    # Get the user name
    type, partition, service, region, account_id, resource_type, resource_id = ctx['config'].parseArn(ctx['config'].get_args()['resourceId'])

    if resource_type != 'user':
        raise Exception('The resource-type was not of type user')

    USERNAME = resource_id

    # Delete the user AWS ref(https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_manage.html#id_users_deleting_cli)

    # Step 1)
    try:
        iam_client.delete_login_profile(UserName=USERNAME, )
    except botocore.exceptions.ClientError as error:
        # Just because the user doesnt have a login profile doesnt mean the user doesnt exist
        pass

    # Step 2)
    access_key_list = iam_client.list_access_keys(UserName=USERNAME, )
    for accessKey in access_key_list['AccessKeyMetadata']:
        iam_client.delete_access_key(UserName=USERNAME, AccessKeyId=accessKey['AccessKeyId'])

    # Step 3)
    signing_certificate_list = iam_client.list_signing_certificates(UserName=USERNAME, )
    for certificate in signing_certificate_list['Certificates']:
        iam_client.delete_signing_certificate(UserName=USERNAME, CertificateId=certificate['CertificateId'])

    # Step 4)
    ssh_key_list = iam_client.list_ssh_public_keys(UserName=USERNAME, )
    for ssh_key in ssh_key_list['SSHPublicKeys']:
        iam_client.delete_ssh_public_key(UserName=USERNAME, SSHPublicKeyId=ssh_key['SSHPublicKeyId'])

    # Step 5)
    service_specific_credential_list = iam_client.list_service_specific_credentials(UserName=USERNAME, )
    for service_specific_credential in service_specific_credential_list['ServiceSpecificCredentials']:
        iam_client.delete_service_specific_credential(UserName=USERNAME,
                                                      ServiceSpecificCredentialId=service_specific_credential[
                                                          'ServiceSpecificCredentialId'])

    # Step 6)
    mfa_list = iam_client.list_mfa_devices(UserName=USERNAME, )
    for mfa in mfa_list['MFADevices']:
        iam_client.deactivate_mfa_device(UserName=USERNAME, SerialNumber=mfa['SerialNumber'])
        iam_client.delete_virtual_mfa_device(SerialNumber=mfa['SerialNumber'])

    # Step 7)
    user_policy_list = iam_client.list_user_policies(UserName=USERNAME, )
    for user_policy_name in user_policy_list['PolicyNames']:
        iam_client.delete_user_policy(UserName=USERNAME, PolicyName=user_policy_name)

    # Step 8)
    attached_user_policy_list = iam_client.list_attached_user_policies(UserName=USERNAME, )
    for attached_policy in attached_user_policy_list['AttachedPolicies']:
        iam_client.detach_user_policy(UserName=USERNAME, PolicyArn=attached_policy['PolicyArn'])

    # Step 9)
    user_group_list = iam_client.list_groups_for_user(UserName=USERNAME, )
    for group in user_group_list['Groups']:
        iam_client.remove_user_from_group(GroupName=group['GroupName'], UserName=USERNAME)

    # Step 10)
    iam_client.delete_user(UserName=USERNAME)

