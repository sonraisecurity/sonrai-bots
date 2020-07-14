import sonrai.platform.aws.arn

import logging

def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')
    config = ctx.config

    resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
    user_name = resource_arn \
        .assert_service("iam") \
        .assert_type("user") \
        .resource

    data = config.get('data')
    access_key_id = None
    if "accessKeyId" in data:
        access_key_id = str(data['accessKeyId'])

    logging.info('deleting accesskey: {} for user: {}'.format(access_key_id, ctx.resource_id))

    iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
