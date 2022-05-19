#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/company_service.py
#
#   CompanyService allows for the details of the high level logic in the app
#   to be abstracted away. It has a tight coupling with both
#   TeamleaderClient and LDAP client
#
# TODO: _load_custom_field_mapping, _get_field_id, get_custom_value, update_or_id and
# migrate_external_id have some code duplication with contact service.
# Now that everything works, we can safely refactor these into a base class like TeamleaderService.
# hint: look in contact service for a more generic update_field and use that here for update_or_id
# best to tackle this when we have added the contact unit tests.
#
# TODO: remove print statements used for debugging...

from enum import Enum
from app.comm.sector_mapping import Sector, SectorMapping
from app.services.contact_service import ContactService
from app.services.tlbase import TLBase
import os


class Category(str, Enum):
    content_partner = 'Content Partner'
    customer = 'Customer'
    service_provider = 'Service Provider'
    meemoo = 'Meemoo'  # used in case of config.yml: company_meemoo_or_id


class CompanyService(TLBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.org_ids = common_clients.org_ids
        self.zendesk = common_clients.zendesk
        self.slack = common_clients.slack
        self._load_custom_field_mapping()
        self.read_custom_labels()
        self.contact_service = ContactService(
            common_clients, self.custom_fields)
        dc_env = os.environ.get('ENVIRONMENT', 'qas').lower()
        self.DN_SUFFIX = f'ou=apps,ou=users,dc={dc_env},dc=viaa,dc=be'

    def _load_custom_field_mapping(self):
        self.custom_fields = self.tlc.list_custom_fields()

    def _get_field_id(self, context, ftype, label):
        for f in self.custom_fields:
            if f['context'] == context and \
                    f['type'] == ftype and \
                    f['label'] == label:
                return f['id']

    def get_custom_value(self, company, ftype, label):
        field_id = self._get_field_id('company', ftype, label)
        all_custom_fields = company.get('custom_fields', [])
        for f in all_custom_fields:
            if f['definition']['id'] == field_id:
                return f['value']

    def update_or_id(self, company, or_id):
        tl_field_id = self._get_field_id(
            'company',
            'single_line',
            self.labels['company_or_id']
        )

        updated_exiting_org_id = False
        for field in company['custom_fields']:
            if field['definition']['id'] == tl_field_id:
                updated_exiting_org_id = True
                field['value'] = or_id

        if not updated_exiting_org_id:
            custom_or_id = {
                'definition': {
                    'type': 'customFieldDefinition',
                    'id': tl_field_id
                },
                'value': or_id
            }
            company['custom_fields'].append(custom_or_id)

        return company

    def kring_value(self, company):
        return self.get_custom_value(
            company,
            'multi_select',
            self.labels['company_kring']
        )

    def kring_filled_in(self, company):
        # find kring value and check if not empty
        kring_value = self.kring_value(company)
        return kring_value is not None and len(kring_value) > 0

    def company_sector(self, company):
        type_org = self.get_custom_value(
            company,
            'single_select',
            self.labels['company_type_organisatie']
        )

        ldap_sector = SectorMapping.lookup_sector(type_org)
        return ldap_sector

    def correct_partner_orgtype(self, company):
        sector = self.company_sector(company)
        return sector is not None

    def correct_customer_orgtype(self, company):
        return self.company_sector(company) is not None

    def relaties_andere_dan_cp(self, company):
        return self.get_custom_value(
            company,
            'multi_select',
            self.labels['relaties_andere_dan_cp']
        )

    def is_dienstafnemer(self, company):
        relatie_values = self.relaties_andere_dan_cp(company)
        if relatie_values is None or len(relatie_values) == 0:
            return False

        return self.labels['company_dienstenafnemer'] in relatie_values

    def is_digitaliserings_partner(self, company):
        relatie_values = self.relaties_andere_dan_cp(company)
        type_org = self.get_custom_value(
            company,
            'single_select',
            self.labels['company_type_organisatie']
        )

        if relatie_values is None or len(relatie_values) == 0:
            return False

        # digitaliseringspartner moet aan deze 2 checks voldoen
        # bij deze is er geen mapping op Sector in LDAP
        # en dus is x-be-viaa-sector leeg hier.
        return (
            self.labels['company_leverancier'] in relatie_values and
            (
                type_org == self.labels['company_digitaliseringsbedrijf'] or
                type_org == self.labels['company_fotograaf']
            )
        )

    def create_company_webhook(self, company):
        print(
            f"create_company_webhook: company found {company['name']}",
            flush=True
        )

        ldap_or_id = None
        if self.kring_filled_in(company):
            # print("DBG: kring value=", self.kring_value(company))
            if self.correct_partner_orgtype(company):
                ldap_or_id = self.add_ldap_company(
                    company, Category.content_partner)
        else:
            print(f"kring not filled in for company {company['id']}")
            if self.is_dienstafnemer(company):
                if self.correct_customer_orgtype(company):
                    ldap_or_id = self.add_ldap_company(
                        company, Category.customer)
                else:
                    self.slack.incorrect_customer_orgtype(company)
            else:
                if self.is_digitaliserings_partner(company):
                    ldap_or_id = self.add_ldap_company(
                        company, Category.service_provider)
                else:
                    print(
                        f"""WARNING: Skipping company create for {company['id']}:
                        it's not a valid kring, digitaliseringspartner or dienstafnemer."""
                    )

        if ldap_or_id is not None:
            company = self.update_or_id(company, ldap_or_id)
            self.tlc.update_company(company)
            return {'status': f'organization added in ldap {ldap_or_id}'}
        else:
            # self.slack.incomplete_company(company)
            return {'status': 'company not complete, not added in ldap'}

    def update_company_webhook(self, company):
        ldap_company = self.ldap.find_company(company['id'])
        if ldap_company:  # company exists in ldap
            if ldap_company.o.value == self.labels['company_meemoo_or_id']:
                self.update_ldap_company(
                    company,
                    Category.meemoo,
                    sector=Sector.cultuur  # set sector to match existing LDAP entry
                )
                return {'status': 'Meemoo company update processed'}

            if self.is_digitaliserings_partner(company):
                self.update_ldap_company(
                    company,
                    Category.service_provider
                )
            else:
                if self.kring_filled_in(company):
                    if self.correct_partner_orgtype(company):
                        self.update_ldap_company(
                            company,
                            Category.content_partner
                        )
                    else:
                        self.slack.wrong_partner(company, ldap_company)
                else:
                    if self.is_dienstafnemer(company):
                        if self.correct_customer_orgtype(company):
                            self.update_ldap_company(
                                company,
                                Category.customer
                            )
                        else:
                            self.slack.wrong_customer(company, ldap_company)
                    else:
                        self.slack.not_a_customer(company, ldap_company)
        else:
            print(
                f"update webhook: {company['id']} not found in LDAP, using create_company_webhook...")
            self.create_company_webhook(company)

        return {'status': 'company update processed'}

    def delete_company_webhook(self, company_uuid):
        ldap_company = self.ldap.find_company(company_uuid)

        if ldap_company:
            self.zendesk.delete_company_ticket(
                self.tlc, self.ldap, company_uuid, ldap_company
            )
            return {
                'status': f'delete company webhook processed for Teamleader ID {company_uuid}'
            }
        else:
            self.slack.deleted_company_not_found(company_uuid)
            return {
                'warning': f"Company with Teamleader ID {company_uuid} was deleted, but not found in LDAP"
            }

    def delete_company(self, company_uuid):
        ldap_org = self.ldap.find_company(company_uuid)

        if not ldap_org:
            self.slack.deleted_company_not_found(company_uuid)
            return {
                'warning': f'could not find company with Teamleader ID {company_uuid} in LDAP'
            }

        ldap_contacts = self.ldap.find_company_contacts(ldap_org.o.value)
        for ldap_contact in ldap_contacts:
            print(
                f"deleting associated company contact {ldap_contact.entry_dn}"
            )
            self.ldap.delete(ldap_contact.entry_dn)

        self.ldap.delete(ldap_org.entry_dn)
        return {
            'status': f'removed company {company_uuid} and associated contacts from LDAP'
        }

    def org_needs_update(self, ldap_org, update_attribs, delete_attribs):
        if len(delete_attribs) > 0:
            return True

        if ldap_org.description.value != update_attribs.get('description', None):
            return True

        if ldap_org.businessCategory.value != update_attribs.get('businessCategory', None):
            return True

        if 'x-be-viaa-sector' in ldap_org.entry_attributes:
            if ldap_org['x-be-viaa-sector'].value != update_attribs.get('x-be-viaa-sector', None):
                return True
        else:
            if update_attribs.get('x-be-viaa-sector', None):
                return True

        return False

    def update_ldap_company(self, company, category: Category, sector: Sector = None) -> str:
        if sector is None:
            # determine with lookup table based on type organisatie
            sector = self.company_sector(company)

        ldap_org = self.ldap.find_company(company['id'])
        update_attributes = {
            'businessCategory': category.value,
            'description': company['name'],
        }

        delete_attributes = []
        if sector is not None:
            update_attributes['x-be-viaa-sector'] = sector.value
        else:
            if 'x-be-viaa-sector' in ldap_org.entry_attributes:
                delete_attributes = ['x-be-viaa-sector']

        if self.org_needs_update(ldap_org, update_attributes, delete_attributes):
            print("updating dn={} new attribs={} del attribs={}".format(
                ldap_org.entry_dn,
                update_attributes,
                delete_attributes
            ), flush=True)

            self.ldap.modify(
                ldap_org.entry_dn,
                update_attributes,
                delete_attributes
            )
        else:
            print("skipping LDAP update for company dn={} because nothing changed".format(
                ldap_org.entry_dn
            ), flush=True)

    def add_ldap_company(self, company, category: Category) -> str:
        # also check if it does not already exist and update instead
        existing_ldap_org = self.ldap.find_company(company['id'])
        if existing_ldap_org is not None:
            print(
                f"create webhook found existing company {company['id']}, updating instead of recreating...")
            self.update_ldap_company(company, category)
            return existing_ldap_org.o.value

        sector = self.company_sector(company)
        or_id = self.org_ids.generate()
        print(
            f"adding {category} in LDAP with generated or_id = {or_id} and sector={sector}"
        )

        dn_string = f'o={or_id},{self.DN_SUFFIX}'
        ldap_org = {
            'objectClass': ['organization', 'x-be-viaa-organization'],
            'businessCategory': category.value,
            'o': or_id,
            'description': company['name'],
            'x-be-viaa-externalUUID': company['id'],
            # 'x-be-viaa-externalId' -> is deprecated for teamleader api v2
        }

        if sector is not None:
            ldap_org['x-be-viaa-sector'] = sector.value

        self.ldap.add(dn_string, ldap_org)

        # now add all linked teamleader contacts also
        company_contacts = self.tlc.company_contacts(company['id'])
        for contact in company_contacts:
            self.contact_service.link_to_company(contact)

        return or_id

    def migrate_external_id(self, ldap_company):
        if 'x-be-viaa-externalUUID' not in ldap_company.entry_attributes:
            if 'x-be-viaa-externalId' in ldap_company.entry_attributes:
                old_id = ldap_company['x-be-viaa-externalId'].value
                company_uuid = self.tlc.get_migrate_uuid('company', old_id)

                if company_uuid is not None:
                    print("migrate_external_id : found company uuid = ",
                          company_uuid, "matching old id=", old_id)

                    update_attributes = {
                        'x-be-viaa-externalUUID': company_uuid
                    }
                    self.ldap.modify(ldap_company.entry_dn, update_attributes)
                    return company_uuid
                else:
                    print(
                        f"Company with external_id={old_id} can't be mapped into uuid")
        else:
            return ldap_company['x-be-viaa-externalUUID'].value

    def sync_or_id(self, ldap_company, company_uuid):
        if company_uuid is None:
            print(f"skipping organization {ldap_company.entry_dn}", flush=True)
            return

        company = self.tlc.get_company(company_uuid)
        if company == []:
            print(
                f"organization {ldap_company.entry_dn} with ID {company_uuid} not found in teamleader")
            return

        ldap_or_id = ldap_company.o.value
        current_company_or_id = self.get_custom_value(
            company, 'single_line', '5.1 - OR-ID'
        )

        if ldap_or_id != current_company_or_id:
            print(
                f"updating or_id to {ldap_or_id} for company {company_uuid}", flush=True)
            company = self.update_or_id(company, ldap_or_id)
            self.tlc.update_company(company)
