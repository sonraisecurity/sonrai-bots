import sonrai.platform.aws.arn

import logging

def run(ctx):
    # Create AWS identity and access management client
    iam_client = ctx.get_client().get('iam')

    data = None
    user_name = None
    access_key_id = None

    data = ctx.get_evidence_policy()
    metadata_list = data.get('metadata')

    for metadata in metadata_list:
        if 'accessKey.userName:' in metadata:
            user_name = metadata.split(":")[1]
            access_key_id = data.get('name')

    logging.info('deleting accesskey: {} for user: {}'.format(access_key_id, user_name))
    iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
