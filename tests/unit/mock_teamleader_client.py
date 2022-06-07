#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/mock_teamleader_client.py
#
#     Mocks teamleader api calls used in company and contact services
#

import json
from tests.unit.mock_client import MockClient

UNKNOWN_CONTACT_UUID = 'non_existing_contact_uuid'
UNKNOWN_COMPANY_UUID = 'non_existing_company_uuid'
LINKED_CONTACT_UUID = 'a602ab6c-112c-088c-907a-45f0d2fc9341'
DIENSTAFNEMER_UUID = '8ac514fc-9247-0280-be7c-9ba5627c9b8e'


class MockTlClient(MockClient):
    def __init__(self):
        super().__init__()
        self.webhook_url = 'webhook_url_mock'
        # self.mock_id = 'teamleader api mock'
        # self.webhook_url = 'http://localhost:8080'

    def list_custom_fields(self):
        # super().method_call(f"list_custom_fields")
        fields_fixture = open('tests/fixtures/custom_fields.json').read()
        return json.loads(fields_fixture)

    def update_company(self, company):
        super().method_call(f"update_company: {company}")

    def update_contact(self, contact):
        super().method_call(f"update_contact: {contact}")

    def secure_route(self, url):
        super().method_call(f"secure_route: {url}")
        return f"{url}?jwtauth=some_jwt_token"

    def company_contacts(self, company_uuid):
        super().method_call(f"company_contacts: {company_uuid}")

        # TODO: add a special case to return a linked contact here
        # for a specific id to test edge_case for linking contacts
        # on new company
        return []  # for now always return empty array

    def get_contact(self, contact_uuid):
        super().method_call(f"get_contact: {contact_uuid}")

        if contact_uuid == UNKNOWN_CONTACT_UUID:
            return None

        contact_fixture = open(
            'tests/fixtures/teamleader/contact_linked_example.json').read()
        contact = json.loads(contact_fixture)
        return contact

    def get_company(self, company_uuid):
        super().method_call(f"get_company: {company_uuid}")
        if company_uuid == UNKNOWN_COMPANY_UUID:
            return []
        else:
            company_fixture = open(
                'tests/fixtures/teamleader/company_updated_addendums.json').read()
            company = json.loads(company_fixture)
            return company

    def list_webhooks(self):
        super().method_call("list_webhooks")

        return [
            {
                "url": "http://localhost:8080/ldap/company/create",
                "types": [
                    "company.added"
                ]
            },
            {
                "url": "http://localhost:8080/ldap/company/delete",
                "types": [
                    "company.deleted"
                ]
            }
        ]

    def register_webhook(self, url, operation):
        super().method_call(
            f"register_webhook url={url}, operation={operation}"
        )
        return {}

    def unregister_webhook(self, url, operation):
        super().method_call(
            f"unregister_webhook url={url}, operation={operation}"
        )
        return {}

    def authcode_callback(self, code, state):
        return {'status': 'code rejected'}
