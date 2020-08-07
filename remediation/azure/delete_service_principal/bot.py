import logging

from azure.graphrbac import GraphRbacManagementClient
from azure.graphrbac.models import GraphErrorException

from sonrai.platform.azure.client import ManagedIdentityClient


def run(ctx):

    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)

    try:
        graphrbac_client.service_principals.delete(object_id=object_id)
        logging.info('deleting Service Principal: {}'.format(object_id))
    except GraphErrorException:
        try:
            graphrbac_client.applications.delete(application_object_id=object_id)
            logging.info('deleting App registration: {}'.format(object_id))
        except GraphErrorException:
            data = ctx.get_policy_evidence()
            metadata_list = data.get('metadata')
            resource_path = None
            has_alternative_name = None
            resource_type = None

            for metadata in metadata_list:
                if 'servicePrincipal.alternativeNames.1:' in metadata:
                    resource_path = metadata.split(":")[1]

                elif 'servicePrincipal.alternativeNames.0' in metadata:
                    has_alternative_name = True

                elif 'servicePrincipal.servicePrincipalType:' in metadata:
                    resource_type = metadata.split(":")[1]

            if resource_type == 'ManagedIdentity' and has_alternative_name:
                managed_identity_client = ctx.get_client().get(ManagedIdentityClient)
                managed_identity_client.delete(object_path=resource_path)
                logging.info('deleting managed identity: {} '.format(resource_path))
            else:
                raise Exception('service principal being deleted is not of type (ManagedIdentity, App registration, or Service principal')



