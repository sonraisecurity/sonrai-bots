import logging

from azure.graphrbac import GraphRbacManagementClient

from sonrai.platform.azure.client import ManagedIdentityClient


def run(ctx):
    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    for object in graphrbac_client.service_principals.list():

        if object.object_id == object_id and object.service_principal_type == 'Application':
            application = next(graphrbac_client.applications.list(filter="appId eq '{}'".format(object.app_id)))
            logging.info('deleting App registration: {}'.format(application.object_id))
            graphrbac_client.applications.delete(application_object_id=application.object_id)
            break

        elif object.object_id == object_id and object.service_principal_type == 'ManagedIdentity':
            managed_identity_client = ctx.get_client().get(ManagedIdentityClient)
            if object.alternative_names[0] == 'isExplicit=True':
                managed_identity_client.delete(object_path=object.alternative_names[1])
                break
