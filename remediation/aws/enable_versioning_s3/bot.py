import botocore
import logging
import sonrai.platform.aws.arn

def run(ctx): 
    s3_client = ctx.get_client().get('s3')

    arr = ctx.resource_id.split(':')
    resource_id = arr[-1]
        
    s3_client.put_bucket_versioning(
        Bucket=resource_id,
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )