import sonrai.platform.aws.arn

import logging


def run(ctx):
    # Create AWS S3 client
    s3_client = ctx.get_client().get('s3')

    bucket_resource_srn = ctx.resource_srn

    bucket_name = bucket_resource_srn.split('/')[-1]

    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True,
        },
    )
    logging.info("Public access is blocked on {} S3 Bucket.".format(bucket_name))
