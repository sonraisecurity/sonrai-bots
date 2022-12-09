import logging
import time
from datetime import datetime

from sonrai import gql_loader


def run(ctx):
    # CONSTANTS
    _maxProjectsToAdd = 1
    gql = gql_loader.queries()

    # Get the ticket data from the context
    ticket = ctx.config.get('data').get('ticket')
    current_time = round(time.time() * 1000)
    now = datetime.now()
    date_stamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    collector_srn = None

    # Loop through each of the custom fields and set the values that we need
    for custom_field in ticket.get('customFields'):
        if 'value' not in custom_field.keys():
            continue

        name = custom_field['name']
        value = custom_field['value']

        if name == 'Collector':
            collector_srn = value

    # GraphQL query for the projects
    variables = '{}'
    logging.info('Searching for all projects')
    r_projects = graphql_client.query(gql['gcpProjects.gql'], variables)

    # GraphQL to get monitored projects on collector already
    variables = '{"srn": "'+collector_srn+'"}'
    logging.info('Searching for already monitored projects on collector: {}'.format(collector_srn))
    r_platform_projects = graphql_client.query(gql['gcpCloudAccounts.gql'], variables)

    project_count = 0
    project_list = None
    for project in r_projects['Accounts']['items']:
        if project_count >= _maxProjectsToAdd:
            # only add _maxProjectsToAdd
            logging.warning("maximum number of projects added for this pass")
            break
            
        # step through all projects to see if it is already added to a collector
        add_projects = True
        project_to_add = project['project_id']
        project_srn = project['srn']

        # check if the projects_to_add is already added
        for existing_projects in r_platform_projects['PlatformCloudAccounts']['items']:
            resource_id = existing_projects['blob']['resourceId']
            if project_to_add == resource_id:
                add_projects = False

        if add_projects:
            # Project doesn't exist on the collector. Adding it here
            project_count += 1  # this is for maximum number of projects to be added
            
            variables = ('{"account": {"containedByAccount":' +
                         '{"add": "' + collector_srn + '"},' +
                         '"cloudType": "gcp",' +
                         '"blob": {' +
                         '"resourceId": "' + project_to_add + '",' +
                         '"resourceType": "project",' +
                         '"runDateTime": ' + str(current_time) +
                         '}' +
                         '}' +
                         '}')
            
            if project_list is None:
                project_list = "- " + project_to_add
            else:
                project_list = project_list + "\\n- " + project_to_add
                
            logging.info('Adding project {}'.format(project_to_add))
            r_add_project = graphql_client.query(gql['addProject.gql'], variables)
            variables = ('{"key":"SonraiBotAdded","value":"' + date_stamp + '","srn":"' + project_srn + '"}')
            r_add_tag = graphql_client.query(gql['addTag.gql'], variables)

    if project_list is not None:
        # build comment for ticket
        comment = "The following projects have been added for monitoring:\\n" + project_list
        gql_loader.add_ticket_comment(ctx, comment)

    # snooze ticket for 2 hours
    gql_loader.snooze_ticket(ctx, hours=2)
    