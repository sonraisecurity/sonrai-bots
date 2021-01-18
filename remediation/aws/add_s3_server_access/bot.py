import logging


def run(ctx):

    s3 = ctx.get_client().get('s3')
    s3_resource = ctx.get_client().resource('s3')

    # Get reource id name
    resource_id = ctx.resource_id

    #Get bucket name
    splited_resource = resource_id.split(":::")
    bucket_name = splited_resource[1]

    #Create a bucket for logging
    logging.info('Creating bucket: {}-audit-data'.format(bucket_name))
    s3.create_bucket(Bucket="{}-audit-data".format(bucket_name))

    #Store all the logging in the new bucket
    logging.info('Logging bucket: {}'.format(bucket_name))
    bucket_logging = s3_resource.BucketLogging(bucket_name)
    bucket_logging.put(
                    BucketLoggingStatus={
                        'LoggingEnabled': {
                            'TargetBucket': "{}-audit-data".format(bucket_name),
                            'TargetPrefix': f'{bucket_name}/'
                        }
                    }
    )