#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/contact_service.py
#
#   ContactService bridges teamleader client and ldap client calls for
#   using in our main application. We also sync back User-ID and contact roles
#   back to teamleader in the update and create hooks.
#

from app.services.tlbase import TLBase
from app.comm.role_mapping import RoleMapping
from ldap3.abstract.entry import Entry
import os


class ContactService(TLBase):
    def __init__(self, common_clients, custom_fields=None):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.zendesk = common_clients.zendesk
        self.slack = common_clients.slack
        self.read_custom_labels()
        if not custom_fields:
            self._load_custom_field_mapping()
        else:
            self.custom_fields = custom_fields

        dc_env = os.environ.get('ENVIRONMENT', 'qas').lower()
        self.DN_SUFFIX = f'ou=apps,ou=users,dc={dc_env},dc=viaa,dc=be'

    def _load_custom_field_mapping(self):
        self.custom_fields = self.tlc.list_custom_fields()

    def _get_field_id(self, label, context='contact'):
        for f in self.custom_fields:
            if f['context'] == context and f['label'] == label:
                return f['id']

    def get_custom_value(self, contact, label):
        field_id = self._get_field_id(label)
        all_custom_fields = contact['custom_fields']
        for f in all_custom_fields:
            if f['definition']['id'] == field_id:
                return f['value']

    def update_field(self, contact, label, value):
        tl_field_id = self._get_field_id(label)

        if tl_field_id is None:
            raise ValueError(
                f"Contact update_field id not found for label={label}")

        if 'custom_fields' not in contact:
            contact['custom_fields'] = []

        updated_existing_value = False
        for field in contact['custom_fields']:
            if field['definition']['id'] == tl_field_id:
                updated_existing_value = True
                field['value'] = value

        if not updated_existing_value:
            custom_field = {
                'definition': {
                    'type': 'customFieldDefinition',
                    'id': tl_field_id
                },
                'value': value
            }
            contact['custom_fields'].append(custom_field)

        return contact

    def update_user_id(self, contact, ldap_entry_uuid):
        contact = self.update_field(
            contact,
            self.labels['contact_user_id'],
            ldap_entry_uuid
        )

        return contact

    def update_roles(self, contact, ldap_roles):
        contact = self.update_field(
            contact,
            self.labels['contact_rollen'],
            ldap_roles
        )

        return contact

    def save_roles_and_user_id(self, ldap_contact, contact):
        contact_roles = self.get_custom_value(
            contact, self.labels['contact_rollen'])
        contact_user_id = self.get_custom_value(
            contact, self.labels['contact_user_id'])
        contact_needs_update = False

        ldap_user_id = ldap_contact.entryUUID.value
        if contact_user_id != ldap_user_id:
            contact = self.update_user_id(contact, ldap_user_id)
            contact_needs_update = True

        ldap_roles = None
        if 'memberOf' in ldap_contact.entry_attributes:
            ldap_roles = RoleMapping.convert(ldap_contact.memberOf.value)
            # make sure the roles arrays are sorted so that
            # the inequality check works correctly.
            ldap_roles.sort()
            contact_roles.sort()
            if contact_roles != ldap_roles:
                print(
                    f"WARNING roles differ. contact_roles={contact_roles} ldap_roles={ldap_roles}")
                contact = self.update_roles(contact, ldap_roles)
                contact_needs_update = True

        # for performance, we only update if values have changed since last sync
        if contact_needs_update:
            print(
                f"updating teamleader contact {contact['id']} roles={ldap_roles} user_id={ldap_user_id}",
                flush=True
            )
            self.tlc.update_contact(contact)

    def contact_name_changed(self, contact, ldap_contact):
        return ldap_contact.givenName.value != contact['first_name'] or \
            ldap_contact.sn.value != contact['last_name']

    def get_contact_company(self, contact):
        if len(contact['companies']) > 1:
            self.slack.multiple_companies_message(contact)
            return

        if len(contact['companies']) < 1:
            self.slack.missing_company_message(contact)
            return

        linked_company = contact['companies'][0]
        company_uuid = linked_company['company']['id']
        return self.ldap.find_company(company_uuid)

    def get_contact_primary_email(self, contact):
        for email in contact['emails']:
            if email['type'] == 'primary':
                return email['email']

        return None

    def update_contact_name(self, contact, ldap_contact):
        return {
            'givenName': contact['first_name'],
            'sn': contact['last_name'],
            'cn': contact['first_name'] + ' ' + contact['last_name']
        }

    def handle_changed_email(self, contact, ldap_contact):
        primary_email = self.get_contact_primary_email(contact)
        if primary_email is None:
            self.slack.missing_email(contact)
        else:
            if not self.check_duplicate_email(contact, primary_email):
                self.zendesk.email_changed_ticket(
                    primary_email, contact, ldap_contact
                )

    def save_user_id(self, ldap_contact, contact):
        contact_user_id = self.get_custom_value(
            contact, self.labels['contact_user_id'])
        contact_needs_update = False

        ldap_user_id = ldap_contact.entryUUID.value
        if contact_user_id != ldap_user_id:
            contact = self.update_user_id(contact, ldap_user_id)
            contact_needs_update = True

        if contact_needs_update:
            print(
                f"updating teamleader entry {contact['id']} setting user_id={ldap_user_id}",
                flush=True
            )
            self.tlc.update_contact(contact)

    def update_contact(self, contact, ldap_contact, new_tl_uuid=None):
        update_attributes = {}
        if self.contact_name_changed(contact, ldap_contact):
            update_attributes = self.update_contact_name(contact, ldap_contact)

        if new_tl_uuid:
            print(f"updating uuid on existing contact to {new_tl_uuid}")
            update_attributes['x-be-viaa-externalUUID'] = new_tl_uuid

        if update_attributes != {}:
            # print(
            #     f"LDAP UPDATE entry:\n {ldap_contact.entry_dn} \n changes: {update_attributes}")
            self.ldap.modify(ldap_contact.entry_dn, update_attributes)

        primary_email = self.get_contact_primary_email(contact)
        if not primary_email or len(primary_email) == 0:
            self.slack.missing_email(contact)
            return

        if ldap_contact.mail != primary_email:
            self.handle_changed_email(contact, ldap_contact)

        # set user_uuid mapping to be correct so that later syncing of roles
        # doesn't break
        self.save_user_id(ldap_contact, contact)

    def update_contact_webhook(self, contact):
        ldap_contact = self.ldap.find_contact(contact['id'])
        # contact also in ldap
        if ldap_contact:
            self.update_contact(contact, ldap_contact)
        else:
            # fix scenario when contact with previously empty email
            # is now updated and thus needs to be added to ldap now
            self.link_to_company(contact)

        return {'status': f"update contact {contact['id']} processed"}

    def handle_technical_user(self, contact, ldap_contact, email, or_id):
        is_technical_user = 'employeeType' in ldap_contact.entry_attributes and \
            ldap_contact.employeeType.value == self.labels['contact_technical_user']

        if is_technical_user:
            self.slack.technical_user_exists(contact, ldap_contact, email)
            return True
        else:
            existing_or_id = ldap_contact.o.value
            if existing_or_id == or_id:
                # set the externalUUID also with an update
                self.update_contact(contact, ldap_contact, contact['id'])
                return True

        # returning false will produce duplicate email zendesk message
        return False

    def check_existing_contact(self, contact, or_id, primary_email):
        # handle moving existing contact from old to new linked_company
        # also handle edge-case where existing contact just needs an update
        existing_ldap_contact = self.ldap.find_contact(contact['id'])
        if existing_ldap_contact:
            existing_or_id = existing_ldap_contact.o.value
            if existing_or_id == or_id:
                # update an existing ldap contact
                print("link_to_company: found and updating existing contact")
                self.update_contact(contact, existing_ldap_contact)
                return True
            else:
                # an unlink webhook has been missed and contact should move now
                print(
                    f"link_to_company: Deleting contact linked to {existing_or_id} and recreating on {or_id}"
                )
                self.ldap.delete(existing_ldap_contact.entry_dn)

        # handle technical users
        existing_contacts = self.ldap.find_contact_by_email(primary_email)
        if type(existing_contacts) == list:
            for c in existing_contacts:
                res = self.handle_technical_user(
                    contact, c, primary_email, or_id)
                if not res:
                    return False

        elif type(existing_contacts) == Entry:
            return self.handle_technical_user(contact, existing_contacts, primary_email, or_id)

        # by returning false a new contact will be created later
        return False

    def check_duplicate_email(self, contact, primary_email):
        # extra sanity check in case email is empty
        if not primary_email or len(primary_email) == 0:
            return False

        other_contact = self.ldap.find_contact_by_email(primary_email)
        if other_contact is not None:
            self.zendesk.duplicate_email_ticket(
                primary_email, contact, other_contact
            )
            return True
        else:
            return False

    def create_ldap_contact(self, contact, primary_email, or_id):
        dn_string = 'mail={},o={},{}'.format(
            self.ldap.escape_chars(primary_email),
            or_id,
            self.DN_SUFFIX
        )

        ldap_contact = {
            'objectClass': ['inetOrgPerson', 'pwmUser', 'top', 'x-be-viaa-person'],
            'o': or_id,
            'cn': contact['first_name'] + ' ' + contact['last_name'],
            'givenName': contact['first_name'],
            'sn': contact['last_name'],
            'x-be-viaa-externalUUID': contact['id'],
            # 'x-be-viaa-externalId' -> is deprecated for teamleader api v2
        }

        # now store contact in ldap
        ldap_result = self.ldap.add(dn_string, ldap_contact)

        # handle errors and respond accordingly
        if ldap_result['result'] == 0:
            # success: update saved roles and the entryUUID back into teamleader
            saved_contact = self.ldap.find_contact(contact['id'])
            self.save_roles_and_user_id(saved_contact, contact)
        elif ldap_result['result'] == 68:
            # entryAlreadyExists
            self.slack.existing_email(primary_email, contact)
        elif ldap_result['result'] == 34:
            # invalidDNSyntax
            self.slack.invalid_email(primary_email, contact)
        else:
            self.slack.ldap_error(primary_email, contact, ldap_result)

    def check_technical_users(self, ldap_org):
        """
        Iterate all users in given ldap organization. If a user has an empty
        externalUUID this is only allowed if it's a Technical User. When
        this is not the case we send out slack messages with warnings we have
        found users we're the external id is missing.
        """
        ldap_contacts = self.ldap.find_company_contacts(ldap_org.o.value)
        for ldap_contact in ldap_contacts:
            if 'x-be-viaa-externalUUID' not in ldap_contact.entry_attributes:
                if 'employeeType' not in ldap_contact.entry_attributes:
                    emp_type = None
                else:
                    emp_type = ldap_contact.employeeType.value

                if emp_type != 'Technical User':
                    self.slack.empty_external_id(ldap_contact)

    def link_to_company(self, contact):
        # first check for edge case where email already exists
        primary_email = self.get_contact_primary_email(contact)
        # older qas version, the self.check_duplicate_email(contact, primary_email)
        # was here as first check DEV-1840

        # find out the contacts company and fetch or_id
        contact_company = self.get_contact_company(contact)
        if not contact_company:
            print(
                f"""Warning contact link_to_company received for {contact['id']}
                but company does not exist in ldap, skipping..."""
            )
            return {'warning': 'contact not added, not linked to 1 company'}

        if not primary_email or len(primary_email) == 0:
            print(
                f"link_to_contact: contact_id={contact['id']} blank primary email.")
            self.slack.missing_email(contact)
            return {'warning': 'link_to_contact: missing email address'}

        or_id = contact_company.o.value
        if self.check_existing_contact(contact, or_id, primary_email):
            return {'status': 'existing contact updated'}

        if self.check_duplicate_email(contact, primary_email):
            # in case of dup or missing company we also send a message here
            contact_company = self.get_contact_company(contact)
            return {'warning': f'skipping ldap add for contact email={primary_email}'}

        self.create_ldap_contact(contact, primary_email, or_id)
        self.check_technical_users(contact_company)

        return {'status': 'contact link_to_company processed'}

    def unlink_from_company(self, contact):
        return self.delete_contact_webhook(contact['id'])

    def delete_contact_webhook(self, contact_uuid):
        ldap_contact = self.ldap.find_contact(contact_uuid)

        if ldap_contact:
            delete_url = '{}&id={}'.format(
                self.tlc.secure_route(
                    f'{self.tlc.webhook_url}/ldap/contact/delete'),
                contact_uuid
            )

            self.zendesk.delete_contact_ticket(
                contact_uuid, ldap_contact, delete_url
            )

            return {
                'status': 'Contact with Teamleader ID {contact_uuid} delete/unlink zendesk ticket created'
            }
        else:
            self.slack.deleted_contact_not_found(contact_uuid)
            return {
                'warning': f"Contact with Teamleader ID {contact_uuid} not found in LDAP"
            }

    def delete_contact(self, contact_uuid):
        ldap_contact = self.ldap.find_contact(contact_uuid)

        tl_contact = self.tlc.get_contact(contact_uuid)
        if tl_contact:
            # clear out user-id and roles in case contact is just unlinked and
            # not fully deleted from teamleader
            tl_contact = self.update_user_id(tl_contact, '')
            tl_contact = self.update_roles(tl_contact, [])
            self.tlc.update_contact(tl_contact)

        if ldap_contact:
            self.ldap.delete(ldap_contact.entry_dn)
            print(f'GET delete_contact: {contact_uuid} removed from LDAP')
            return {'status': f'delete_contact: {contact_uuid} removed from LDAP'}
        else:
            print(f'GET delete_contact: {contact_uuid} not found in LDAP')
            self.slack.deleted_contact_not_found(contact_uuid)
            return {'error': f'delete_contact: contact {contact_uuid} not found in LDAP'}

    def migrate_external_id(self, ldap_contact):
        if 'x-be-viaa-externalUUID' not in ldap_contact.entry_attributes:
            if 'x-be-viaa-externalId' in ldap_contact.entry_attributes:
                old_id = ldap_contact['x-be-viaa-externalId'].value
                contact_uuid = self.tlc.get_migrate_uuid('contact', old_id)

                if contact_uuid is not None:
                    print("migrate_external_id : found contact uuid = ",
                          contact_uuid, "matching old id=", old_id)

                    update_attributes = {
                        'x-be-viaa-externalUUID': contact_uuid
                    }
                    self.ldap.modify(ldap_contact.entry_dn, update_attributes)
                    return contact_uuid
                else:
                    self.slack.failed_external_id(old_id)
        else:
            return ldap_contact['x-be-viaa-externalUUID'].value

    def sync_roles_and_user_id(self, ldap_contact, contact_uuid):
        if contact_uuid is None:
            self.slack.failed_sync_roles(contact_uuid, ldap_contact)
            return

        contact = self.tlc.get_contact(contact_uuid)
        if contact == []:
            self.slack.sync_roles_contact_missing(contact_uuid)
            return

        self.save_roles_and_user_id(ldap_contact, contact)
