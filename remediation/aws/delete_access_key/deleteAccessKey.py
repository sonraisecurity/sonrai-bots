import sonrai.aws


def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')
    config = ctx.config

    resource_arn = sonrai.aws.parse_arn(ctx.resource_id)
    user_name = resource_arn \
        .assert_service("iam") \
        .assert_type("user") \
        .resource

    data = config.get_unstructured_data()
    access_key_id = None
    if "access_key_id" in data:
        access_key_id = str(data['access_key_id'])

    iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
