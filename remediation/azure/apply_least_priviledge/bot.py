import logging
import uuid
import re

from azure.mgmt.authorization import AuthorizationManagementClient
from msrestazure.azure_exceptions import CloudError


def run(ctx):
    for data in ctx.get_policy_evidence_data():
        with SonraiPolicy.parse(ctx, data) as policy:
            policy.enforce()


class SonraiPolicy:
    @staticmethod
    def parse(ctx, data):
        policy = data.get("policy", None)
        if not policy:
            raise ValueError("expected: data.policy")
        policy_type = policy.get("type", None)
        policy_type = policy_type if policy_type else 'attach'
        credentials = ctx.get_client().credential
        if policy_type == 'attach':
            return SonraiAttachPolicy(data, credentials)
        elif policy_type == 'detach':
            return SonraiDetachPolicy(data, credentials)
        raise ValueError("Unsupported policy type: {}".format(policy_type))

    def __init__(self, data, credentials):
        self.log = logging.getLogger()
        self.credentials = credentials
        #: Identity/Principal
        self.identity_resource_id = data.get('resourceId', None)
        if not self.identity_resource_id:
            raise ValueError("expected: data.resourceId")
        #: Role Assignment
        self.existing_role_assignment_id = data.get("policyResourceId", None)
        if not self.existing_role_assignment_id:
            raise ValueError("expected: data.policyResourceId")
        self.subscription_id = self._get_subscription_id(self.existing_role_assignment_id)

    def __enter__(self):
        self.client = AuthorizationManagementClient(self.credentials, self.subscription_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        client = self.client
        if client is not None:
            try:
                client.close()
            finally:
                self.client = None

    def enforce(self):
        raise NotImplementedError()

    @staticmethod
    def _get_subscription_id(role_assignment_id):
        #: TODO Update ParsedPolicyId to allow for non ARM resources
        parts = role_assignment_id.split('/', maxsplit=6)
        if len(parts) != 7 \
                or parts[0] != '' \
                or parts[1].lower() != 'subscriptions' \
                or parts[3].lower() != 'providers' \
                or parts[4].lower() != 'microsoft.authorization' \
                or parts[5].lower() != 'roleassignments':
            raise ValueError("Invalid resource id: {}".format(role_assignment_id))
        return parts[2]

    def _delete_role_assignment(self, role_assignment_id):
        self.log.info("Deleting role assignment if it exists: {}".format(role_assignment_id))
        try:
            self.client.role_assignments.delete_by_id(role_assignment_id)
        except CloudError as e:
            if e.status_code != 204:
                raise e
            self.log.info("Role assignment does not exist")
            return
        self.log.info("Role assignment deleted: {}".format(role_assignment_id))


class SonraiDetachPolicy(SonraiPolicy):
    def __init__(self, data, credentials):
        super().__init__(data, credentials)

    def enforce(self):
        self._delete_role_assignment(self.existing_role_assignment_id)


class SonraiAttachPolicy(SonraiPolicy):
    def __init__(self, data, credentials):
        super().__init__(data, credentials)
        #: Role Definition
        role_definitions = data.policy.get('roleDefinition', [])
        if not isinstance(role_definitions, list):
            role_definitions = [role_definitions]
        if len(role_definitions) != 1:
            raise ValueError('expected exactly one: data.policy.roleDefinition')
        self.role_definition = role_definitions[0].as_plain_ordered_dict()
        self.role_definition_name = 'Sonrai Reduced Role - {}'.format(self.identity_resource_id)
        self.role_definition_description = self.role_definition_name
        self.role_definition_scope = self._extract_role_definition_scope(self.role_definition)
        #: Role Assignment
        self.role_assignment_name = self.role_definition_name
        self.role_assignment_scope = self.role_definition_scope

    def enforce(self):
        rd_id = self._create_or_update_role_definition()
        self._create_or_update_role_assignment(rd_id)
        self._delete_role_assignment(self.existing_role_assignment_id)

    def _create_or_update_role_assignment(self, role_definition_id):
        ra_scope = self.role_assignment_scope
        ra_principal = self.identity_resource_id
        existing_ra = None
        self.log.info("Searching for existing Role Assignment matching: scope={}, assigned_to={}, role_definition_id={}"
                      .format(ra_scope, ra_principal, role_definition_id))
        for ra in self.client.role_assignments.list(
                filter="atScope() and assignedTo('{}')".format(self.identity_resource_id)
        ):
            if ra.role_definition_id == role_definition_id:
                existing_ra = ra
                break
        if existing_ra:
            ra_guid = existing_ra.name  # name == guid
            self.log.info("Found existing Role Assignment: {}".format(existing_ra.id))
        else:
            ra_guid = uuid.uuid4()
            self.log.info("No existing Role Assignment found, a new one will be created")
        properties = {
            "roleDefinitionId": role_definition_id,
            "principalId": self.identity_resource_id
        }
        ra = self.client.role_assignments.create(ra_scope, ra_guid, properties)
        self.log.info("Created/Updated Role Assignment: {}".format(ra.id))
        return ra.id

    _INVALID_PERMISSION_PATTERN = re.compile(
        '\'([^\']+)\' does not match any of the actions supported by the providers\\.')

    def _create_or_update_role_definition(self):
        rd_scope = self.role_definition_scope
        rd_name = self.role_definition_name
        rd_description = self.role_definition_description
        rd_properties = self.role_definition['properties']
        existing_rd = None
        self.log.info("Searching for existing Role Definition with role name: \"{}\"".format(rd_name))
        for rd in self.client.role_definitions.list(
                scope=rd_scope,
                filter="type eq 'CustomRole'"
        ):
            if rd.role_name == rd_name:
                existing_rd = rd
                break
        if existing_rd:
            rd_guid = existing_rd.name  # name == guid
            self.log.info("Found existing Role Definition: {}".format(existing_rd.id))
        else:
            rd_guid = uuid.uuid4()
            self.log.info("No existing Role Definition found, a new one will be created")
        # Replace some provided properties
        rd_properties['roleName'] = rd_name
        rd_properties['description'] = rd_description
        self._set_permissions(rd_properties)
        while True:
            try:
                rd = self.client.role_definitions.create_or_update(
                    scope=rd_scope,
                    role_definition_id=rd_guid,
                    role_definition=rd_properties
                )
                break
            except CloudError as e:
                if e.status_code != 400:
                    raise
                # Was an invalid permission supplied?
                # The Sonrai platform detects more permissions than
                # are accepted by the Role Definition API.
                # Exclude them from the request, and re-issue it
                m = self._INVALID_PERMISSION_PATTERN.search(e.message)
                if not m:
                    raise
                # Remove the invalid permission from the request
                invalid_permission = m.group(1)
                self.log.info("Excluding invalid permission: {}".format(invalid_permission))
                modified = False
                for permissions in rd_properties['permissions']:
                    for k in ('actions', 'notActions', 'dataActions', 'notDataActions'):
                        if k not in permissions:
                            continue
                        permission_set = permissions[k]
                        if invalid_permission in permission_set:
                            permission_set.remove(invalid_permission)
                            modified = True
                # If the permission was not found in the request, raise
                if not modified:
                    raise
        self.log.info("Created/Updated Role Definition: {}".format(rd.id))
        return rd.id

    @staticmethod
    def _set_permissions(rd_properties):
        # Replace list of permissions with a set() for easier manipulation
        for permissions in rd_properties['permissions']:
            for k in ('actions', 'notActions', 'dataActions', 'notDataActions'):
                if k not in permissions:
                    continue
                s = set()
                for permission in permissions[k]:
                    if permission.lower().startswith('microsoft.iotspaces'):
                        continue
                    s.add(permission)
                permissions[k] = s

    @staticmethod
    def _extract_role_definition_scope(policy_role_definition):
        properties = policy_role_definition.get('properties', {})
        if not properties:
            raise ValueError("expected: data.policy.roleDefinition.properties")
        assignable_scopes = properties.get('assignableScopes', [])
        if not assignable_scopes or len(assignable_scopes) != 1:
            raise ValueError("expected exactly 1 entry for: data.policy.roleDefinition.properties.assignableScopes")
        return assignable_scopes[0]
