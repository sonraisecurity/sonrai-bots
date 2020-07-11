from azure.graphrbac import GraphRbacManagementClient


def run(ctx):

    object_id = ctx.resource_id

    graphrbac_client = ctx.get_client().get(GraphRbacManagementClient)
    graphrbac_client.applications.delete(application_object_id='28e372b9-a701-414a-a419-5300dc7eb88a')