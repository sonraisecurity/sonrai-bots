import logging


def run(ctx):

    resource_id = ctx.resource_id
    project = resource_id.split('/')[4]
    service_account = resource_id.split('/')[6]

    service = ctx.get_client().get('iam', 'v1')

    logging.info('deleting service account: {} from project: {}'.format(service_account, project))
    response = service.projects().serviceAccounts().delete(name='projects/{project}/serviceAccounts/'.format(project=project) + service_account).execute()

