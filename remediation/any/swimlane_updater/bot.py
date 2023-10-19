import datetime
import logging
import time
from datetime import datetime
from sonrai import gql_loader

def run(ctx):
    # Create GraphQL client
    graphql_client = ctx.graphql_client()
    ticket = ctx.config.get('data').get('ticket')

    # load results of saved search - see graphql/Users.sql
    logging.info('Querying Swimlanes with proper tagging')

    # Swimlane update search
    sus_results = graphql_client.query('''
    query swimlane {
      Swimlanes ( where: { tags: { op: CONTAINS value: "|update-search" } } )
      {
        count
        items(limit: -1) {
          title
          srn
          tags
          accounts
          resourceIds
        }
      }
    }
    ''')
    
    # Iterate through each swimlane
    for item in sus_results['Swimlanes']['items']:
        # Dictionary for update
        # Keys: R = Resource IDs, A = Accounts, N = Names, T = Tags
        updates = {"R": [], "A": [], "N": [], "T": []}

        # Dictionary for swimlane
        # Keys: R = Resource IDs, A = Accounts, N = Names, T = Tags
        swimlane = {"R": [], "A": [], "N": [], "T": []}

        # store the swimlane accounts
        if item.get('accounts'):
            # Create a list to store these
            accountList = list()
            for account in item['accounts']:
                accountList.append(account)

            # add the temp list into the swimlane dict
            if accountList:
                swimlane['A'] = accountList

        # store the swimlane resources
        if item.get('resourceIds'):
            # Create a list to store these
            resourceList = list()
            for resource in item['resourceIds']:
                resourceList.append(resource)

            # add the temp list into the swimlane dict
            if resourceList:
                swimlane['R'] = resourceList

        # Check tags for "update-search" key and iterate
        if item.get('tags'):
            for tag in item['tags']:
                data = tag.split(":")
                if '|update-search' in str(data[0][1:]):
                    search = str(data[1][:-1])
                    search_keys = str(data[0][1:]).split("|")
                    search_type = str(search_keys[0]).upper()
                    search_group = str(search_keys[1])
                    return_value = str(search_keys[2])

                    # some generic test for a valid search string
                    if search and search.isascii() and search != '*' and len(search_keys) == 4:
                        # Execute the search
                        logging.info("Running search from swimlane tag: " + search)
                        search_results = graphql_client.query('{{ExecuteSavedQuery {{Query (name:"{search}" )}}}}'.format(search=search))

                        try:
                            for row in search_results['ExecuteSavedQuery']['Query'][search_group]['items']:
                                tempR = list(updates[search_type])
                                if search_type == 'R':
                                    tempR.append('*' + row[return_value] + '*')
                                else:
                                    tempR.append(row[return_value])

                                # Remove duplicates: list->set->list
                                updates[search_type] = list(set(tempR))

                        except KeyError:
                            logging.error("Invalid Search or Search_Group in tag: {search_keys}:{search}".format(search_keys=data[0], search=data[1]))

                    else:
                        logging.error("Invalid Search or Search_Group in tag: {search_keys}:{search}".format(search_keys=data[0], search=data[1]))

        # create the REMOVE and ADD arrays and update the swimlane
        remove_resourceIds = list()
        add_resourceIds = list()
        remove_accounts = list()
        add_accounts = list()

        for key in updates:
            if updates[key]:
                add_resourceIds = list(set(updates[key]) - set(swimlane[key]))
                remove_resourceIds = list(set(swimlane[key]) - set(updates[key]))

        for key in swimlane:
            if swimlane[key]:
                add_accounts = list(set(updates[key]) - set(swimlane[key]))
                remove_accounts = list(set(swimlane[key]) - set(updates[key]))
                
        # Build the mutations

        # Resources
        add_resourceIds = str(add_resourceIds).replace("'", '"')
        remove_resourceIds = str(remove_resourceIds).replace("'", '"')
        resource = '{{ resourceIds: {{ add: {add}, remove: {remove} }}'.format(add=add_resourceIds, remove=remove_resourceIds)

        # Accounts
        add_accounts = str(add_accounts).replace("'", '"')
        remove_accounts = str(remove_accounts).replace("'", '"')
        accounts = ' accounts: {{ add: {add}, remove: {remove} }} }}'.format(add=add_accounts, remove=remove_accounts)

        swimlane_mutation = 'mutation updateSwimlane {{ UpdateSwimlane(srn: "{srn}", value: {resource} {accounts} ) {{ srn }}}}'.format(srn=item['srn'], resource=resource, accounts=accounts)
        if len(add_resourceIds) > 2 or len(remove_resourceIds) > 2 or len(add_accounts) > 2 or len(remove_accounts) > 2:
            logging.info("Preparing to Update Swimlane: " + item['title'])
            swimlane_results = graphql_client.query(swimlane_mutation)

            # build comment for ticket
            comment = "Swimlane Update: {}".format(item['title'])

            if len(add_resourceIds) > 2:
                comment += "\\nAdding Resource Ids: {}".format(add_resourceIds)
            if len(remove_resourceIds) > 2:
                comment += "\\nRemoving Resource Ids: {}".format(remove_resourceIds)
            if len(add_accounts) > 2:
                comment += "\\nAdding Accounts: {}".format(add_accounts)
            if len(remove_accounts) > 2:
                comment += "\\nRemoving Accounts: {}".format(remove_accounts)
                
            comment = comment.replace('"', "'")
            logging.info(comment)
            gql_loader.add_ticket_comment(ctx, comment)
        else:
            logging.info("Nothing to do for Swimlane: " + item['title'])

    # update the ticket runtime
    current_time = datetime.now()
    date_stamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
    update_ticket_mutation = '''mutation updateTicket {{
  UpdateTicket(
    input: {{
      ticketSrn: "{ticket_srn}"
      customFields: {{ name: "last_run", value: "{last_run_timestamp}" }}
    }}
  ) {{
   srn
  }}
}}
'''.format(ticket_srn=ticket.get('srn'), last_run_timestamp=date_stamp)
    
    custom_field_results = graphql_client.query(update_ticket_mutation)
