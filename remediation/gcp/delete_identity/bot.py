import logging


def run(ctx):
    resource_id = ctx.resource_id

    if resource_id.split('/')[5] == 'serviceAccounts':
        project = resource_id.split('/')[4]
        service_account = resource_id.split('/')[6]

        service = ctx.get_client().get('iam', 'v1')

        logging.info('deleting service account: {} from project: {}'.format(service_account, project))
        service.projects().serviceAccounts().delete(name='projects/{project}/serviceAccounts/'.format(project=project) + service_account).execute()

    else:
        organization_id = None
        # convert organization to id
        organization = resource_id.split('/')[4]
        cloudresourcemanager_v1beta1 = ctx.get_client().get('cloudresourcemanager', 'v1beta1')
        request = cloudresourcemanager_v1beta1.organizations().list()
        response = request.execute()
        for element in response.get('organizations'):
            if element.get('displayName') == organization:
                organization_id = element.get('organizationId')

        username = resource_id.split('/')[6]

        cloudresourcemanager_v1 = ctx.get_client().get('cloudresourcemanager', 'v1')

        # Organization level permissions
        resource = 'organizations/' + organization_id
        request = cloudresourcemanager_v1.organizations().getIamPolicy(resource=resource)
        policy = request.execute()
        logging.info('removing all bindings for user: {} in organization: {} from organization level'.format(username,
                                                                                                             organization_id))
        cloudresourcemanager_v1.organizations().setIamPolicy(resource=resource,
                                                             body=get_removed_policy_binding(policy, username)).execute()

        # Folder level permissions
        cloudresourcemanager_v2 = ctx.get_client().get('cloudresourcemanager', 'v2')
        response = cloudresourcemanager_v2.folders().list(parent=resource).execute()

        for folder in response.get('folders'):
            policy = cloudresourcemanager_v2.folders().getIamPolicy(resource=folder['name']).execute()
            logging.info('removing all bindings for user: {} in folder: {}'.format(username, folder['name']))
            cloudresourcemanager_v2.folders().setIamPolicy(resource=folder['name'],
                                                           body=get_removed_policy_binding(policy, username)).execute()

        # Project level permissions
        request = cloudresourcemanager_v1.projects().list()
        response = request.execute()

        for project in response.get('projects'):
            policy = cloudresourcemanager_v1.projects().getIamPolicy(resource=project['projectId']).execute()
            logging.info('removing all bindings for user: {} in projectId: {}'.format(username, project['projectId']))
            cloudresourcemanager_v1.projects().setIamPolicy(resource=project['projectId'],
                                                            body=get_removed_policy_binding(policy, username)).execute()


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
