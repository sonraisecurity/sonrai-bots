import datetime
import logging
import time
from datetime import datetime, timedelta

from sonrai import gql_loader


def run(ctx):
    # create gql_loader queries
    gql = gql_loader.queries()

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # load results of saved search - see graphql/Users.sql
    logging.info('Loading User Results')
    data = graphql_client.query(gql['Users.gql'])

    # --- Custom Variables (Yes you can change the ones in the else: section)
    days = 90  # how many days to look for inactive users
    keep_sonrai_security_users = True  # Do you want to keep @sonraisecurity users (Generally Support and PS)
    never_disable = ['joe@smith.com']  # List of users to never disable ['user1@tld.com','user2@tld.com']
    
    # Loop through each of the custom fields and set the values that we need if the Custom Ticket exist
    custom_ticket = ctx.config.get('data').get('ticket').get('customFields')
    if custom_ticket:
        for custom_field in custom_ticket:
            if 'value' not in custom_field.keys():
                continue

            name = custom_field['name']
            value = custom_field['value']

            if name == 'Disable in-active users after this many days':
                days = int(value)

            if name == 'Keep Sonrai-Security Users':
                keep_sonrai_security_users = value

            if name == 'Never Disable These Users':
                never_disable = value
                  
    # --- End of Custom Variables

    # some time foolery
    pattern = '%Y-%m-%d %H:%M:%S'
    today = datetime.now()
    n_ago = today - timedelta(days=days)
    new_days_ago = n_ago.strftime(pattern)
    n_days_epoch = int(time.mktime(time.strptime(new_days_ago, pattern)))

    if data:
        try:
            logging.info('Checking for users past {0} Days last login'.format(days))
            for row in data['SonraiUsers']['items']:

                # Check our never_disable list
                if row['email'] in never_disable:
                    continue

                # Check if we should remove a Sonrai Security user
                if '@sonraisecurity' in row['email'] and keep_sonrai_security_users:
                    continue

                # Check if the users last login exceeds required timeframe: date - n_days_epoch
                if int(row['lastLogin']) > int(n_days_epoch):
                    continue

                logging.info('Disabling User: {0} ({1})'.format(row['name'], row['email']))

                try:
                    mutation_variables = {"updateGuy": {"srn": row['srn'], "isActive": "false"}}
                    return_value = graphql_client.query(gql['updateSonraiGuy.gql'], mutation_variables)
                except Exception as e:
                    return_value = None
                    logging.info('Something went wrong disabling User: {0} ({1}) - {2}'.format(row['name'], row['email'], e))

                if return_value:
                    logging.info('Disabled User: {0} ({1})'.format(return_value['UpdateSonraiUsers']['items'][0]['name'], return_value['UpdateSonraiUsers']['items'][0]['email']))

            logging.info('Users iteration completed')

        except Exception as e:
            logging.info("General Error: " + repr(e))
