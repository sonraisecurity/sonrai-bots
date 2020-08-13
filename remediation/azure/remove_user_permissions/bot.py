import logging

from azure.graphrbac import GraphRbacManagementClient
from azure.graphrbac.models import GraphErrorException

from sonrai.platform.azure.client import ManagedIdentityClient


def run(ctx):
    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    try:
        graphrbac_client.users.get(upn_or_object_id=object_id)
        logging.info('deleting user: {}'.format(object_id))
        graphrbac_client.users.delete(upn_or_object_id=object_id)
    except GraphErrorException as e:
        if e.error.code == 'Request_ResourceNotFound':
            pass
        else:
            raise e

    for object in graphrbac_client.service_principals.list():
        if object.object_id == object_id:
            if object.service_principal_type == 'Application':
                application = next(graphrbac_client.applications.list(filter="appId eq '{}'".format(object.app_id)))
                logging.info('deleting App registration: {}'.format(application.object_id))
                graphrbac_client.applications.delete(application_object_id=application.object_id)
                return
            elif object.service_principal_type == 'ManagedIdentity':
                managed_identity_client = ctx.get_client().get(ManagedIdentityClient)
                if object.alternative_names[0] == 'isExplicit=True':
                    logging.info('deleting Managed Identity: {}'.format(object.alternative_names[1]))
                    managed_identity_client.delete(object_path=object.alternative_names[1])
                    return
                raise Exception(
                    'object_id: {} is a ManagedIdentity, but had no explicit alternative name'.format(object_id))

    raise Exception('object_id: {} did not match any service principals or users'.format(object_id))
