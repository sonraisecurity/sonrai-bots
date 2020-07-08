def run(ctx):
    service = ctx.get_client().get('iam', 'v1')

    project = 'development-test-245814'
    email = 'joshua-delete-service-account@development-test-245814.iam.gserviceaccount.com'

    response = service.projects().serviceAccounts().delete(name='projects/{project}/serviceAccounts/'.format(project=project) + email).execute()