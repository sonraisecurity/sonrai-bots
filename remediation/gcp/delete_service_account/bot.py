import logging


def run(ctx):
    # Get data
    email = None
    project = None

    policy_evidence = ctx.get_evidence_policy()
    data = policy_evidence.get('data').get('Users').get('items')
    if data:
        data = data[0]

    metadata_list = data.get('metadata')

    for metadata in metadata_list:
        if 'serviceAccount.email:' in metadata:
            email = metadata.split(":")[1]
        elif 'serviceAccount.projectId:' in metadata:
            project = metadata.split(":")[1]

    service = ctx.get_client().get('iam', 'v1')

    logging.info('deleting service account: {} from project: {}'.format(email, project))
    response = service.projects().serviceAccounts().delete(name='projects/{project}/serviceAccounts/'.format(project=project) + email).execute()