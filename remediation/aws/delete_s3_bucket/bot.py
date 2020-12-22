import sonrai.platform.aws.arn

import logging


def run(ctx):
    # Create AWS S3 client
    s3_client = ctx.get_client().get('s3')

    bucket_resource_srn = ctx.resource_srn

    bucket_name = bucket_resource_srn.split('/')[-1]

    # delete all objects from the bucket first
    response = s3_client.list_objects(Bucket=bucket_name)
    # there could be several iterations if a bucket contains large amount of objects
    logging.info('Deleting objects from S3 bucket {}.'.format(bucket_name))
    while response.get('Contents', None):
        for item in response['Contents']:
            s3_client.delete_object(Bucket=bucket_name, Key=item["Key"])
        response = s3_client.list_objects(Bucket=bucket_name)
    logging.info('Deleting S3 bucket {}.'.format(bucket_name))
    s3_client.delete_bucket(Bucket=bucket_name)
