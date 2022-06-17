import sonrai.platform.aws.arn
import logging
import json


def run(ctx):
    # Create AWS S3 client
    iam_client = ctx.get_client().get('iam')
    iam_policy_resource_srn = ctx.resource_srn
    policy_name = iam_policy_resource_srn.split('/')[-1]

    try:
        iam_client.update_account_password_policy(
            PasswordReusePrevention=23,  # last 23 passwords

        )
        logging.info(
            f"Updated IAM password policy with CIS AWS Foundations "
            f"requirements for Account '{policy_name}'."
        )

    except:
        logging.error(
            f"Could not update IAM password policy for Account '{policy_name}'."
        )
        logging.error(sys.exc_info()[1])
