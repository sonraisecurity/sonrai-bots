import logging


def run(ctx):
    # Get data for bot from config
    config = ctx.config
    data = config.get('data').get('data')
    organization_id = data.get('organizationId')
    username = data.get('username')

    cloudresourcemanager_v1 = ctx.get_client().get('cloudresourcemanager', 'v1')

    # Organization level permissions
    resource = 'organizations/' + organization_id
    request = cloudresourcemanager_v1.organizations().getIamPolicy(resource=resource)
    policy = request.execute()
    logging.info('removing all bindings for user: {} in organization: {} from organization level'.format(username, organization_id))
    cloudresourcemanager_v1.organizations().setIamPolicy(resource=resource, body=get_removed_policy_binding(policy, username)).execute()

    # Folder level permissions
    cloudresourcemanager_v2 = ctx.get_client().get('cloudresourcemanager', 'v2')
    response = cloudresourcemanager_v2.folders().list(parent=resource).execute()

    for folder in response.get('folders'):
        policy = cloudresourcemanager_v2.folders().getIamPolicy(resource=folder['name']).execute()
        logging.info('removing all bindings for user: {} in folder: {}'.format(username,folder['name']))
        cloudresourcemanager_v2.folders().setIamPolicy(resource=folder['name'], body=get_removed_policy_binding(policy, username)).execute()


    # Project level permissions
    request = cloudresourcemanager_v1.projects().list()
    response = request.execute()

    for project in response.get('projects'):
        policy = cloudresourcemanager_v1.projects().getIamPolicy(resource=project['projectId']).execute()
        logging.info('removing all bindings for user: {} in projectId: {}'.format(username, project['projectId']))
        cloudresourcemanager_v1.projects().setIamPolicy(resource=project['projectId'], body=get_removed_policy_binding(policy, username)).execute()


def get_removed_policy_binding(policy, username):
    bindings = []
    if 'bindings' in policy:
        for binding in policy['bindings']:
            try:
                binding.get('members').remove(username)
                bindings.append(binding)
            except Exception:
                bindings.append(binding)

        policy['bindings'] = bindings

        set_iam_policy_request_body = {
            "policy": policy
        }

        return set_iam_policy_request_body

    return None
