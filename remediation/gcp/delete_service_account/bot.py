import logging


def run(ctx):
    # Get data for bot from config
    config = ctx.config
    data = config.get('data').get('data')
    project = data.get('project')
    email = data.get('email')

    service = ctx.get_client().get('iam', 'v1')

    logging.info('deleting service account: {} from project: {}'.format(email, project))
    response = service.projects().serviceAccounts().delete(name='projects/{project}/serviceAccounts/'.format(project=project) + email).execute()