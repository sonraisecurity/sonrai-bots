import sonrai.platform.aws.arn

def run(ctx):

  # Get role name
  resource_arn = sonrai.platform.aws.arn.parse(ctx.resource_id)
  instance_id = resource_arn \
    .assert_service("rds") \
    .assert_type("db") \
    .name

  rds_client = ctx.get_client().get('rds', resource_arn.region)

  rds_client.start_db_instance(DBInstanceIdentifier=instance_id)
