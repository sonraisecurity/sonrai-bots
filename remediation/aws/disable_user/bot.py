import botocore
import logging
import sonrai.platform.aws.arn

def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    # Verify that the resource_id is an IAM User
    #   arn:aws:iam::123271222534:user/testUser
    resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    user_name = resource_arn \
        .assert_service("iam") \
        .assert_type("user") \
        .name

    # Delete login profile
    try:
        iam_client.delete_login_profile(UserName=user_name,)
    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error")
        # AWS User may not have a login profile already
        if not error or error.get("Code") != "NoSuchEntity":
            raise e

    # Delete access keys
    access_key_list = iam_client.list_access_keys(UserName=user_name, )
    for accessKey in access_key_list['AccessKeyMetadata']:
        iam_client.delete_access_key(UserName=user_name, AccessKeyId=accessKey['AccessKeyId'])
