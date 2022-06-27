#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/mock_ldap_client.py
#
#     Mocks ldap calls used in company and contact services
#     and trigger various scenarios to send out zendesk and slack messages etc.

import json
import uuid

from tests.unit.mock_client import MockClient
from dataclasses import dataclass, field


UNKNOWN_LDAP_UUID = 'non_existing_ldap_externalid'
MOCK_DN_STRING = 'dn: o=OR-ddeeff2,ou=apps,ou=users,dc=qas,dc=viaa,dc=be'
MOCK_CONTACT_DN_STRING = 'dn: mail=schreppers_anytest@gmail.com,o=OR-ddeeff2,ou=apps,ou=users,dc=qas,dc=viaa,dc=be'
NEW_COMPANY_UUID = '8ac514fc-9247-0280-be7c-9ba5627c9b8e'


class KeyValMock:
    def __init__(self, mock_value):
        self.mock_value = mock_value

    @property
    def value(self):
        return self.mock_value


@dataclass
class LdapEntryMock:
    '''Mock class of LDAP3 Entry of ldap3 library'''

    entry_x_be_viaa_externalUUID: str
    entryUUID: uuid.UUID = uuid.uuid4()
    entryOID: int = 1234
    entryDescription: str = 'organization description'
    entry_dn: str = MOCK_DN_STRING
    attributes: dict = field(default_factory=dict)
    or_id: str = 'OR-aabbcc1'

    @property
    def o(self):
        return KeyValMock(self.or_id)

    @property
    def description(self):
        return KeyValMock('BVBA Anykey')

    @property
    def businessCategory(self):
        return KeyValMock('Customer')

    @property
    def entry_attributes(self):
        return [
            'createTimestamp', 'businessCategory', 'modifiersName',
            'creatorsName', 'modifyTimestamp', 'entryCSN', 'structuralObjectClass',
            'x-be-viaa-externalUUID', 'x-be-viaa-sector', 'x-be-viaa-externalId',
            'subschemaSubentry', 'hasSubordinates', 'description', 'objectClass',
            'entryUUID', 'seeAlso', 'o'
        ]

    def entry_to_json(self) -> str:
        return json.dumps(self.attributes)

    def __init__(self, company_id):
        self.entry_x_be_viaa_externalUUID = company_id

    def __getitem__(self, ldap_attribute_key):
        if ldap_attribute_key == 'x-be-viaa-sector':
            return KeyValMock('Cultuur')
        if ldap_attribute_key == 'x-be-viaa-externalUUID':
            return KeyValMock('1b2ab41a-7f59-103b-8cd4-1fcdd5140767')
        # fallback mode for when in sync call only an externalId is present
        if ldap_attribute_key == 'x-be-viaa-externalId':
            return KeyValMock(123)


class MockLdapClient(MockClient):
    def __init__(self):
        super().__init__()

    def connection(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def find_company_by_uuid(self, company_uuid):
        print(f"MOCK find_company uuid={company_uuid}", flush=True)
        super().method_call(f"find_company: {company_uuid}")

        # simulate a non-existing company in ldap
        if company_uuid == NEW_COMPANY_UUID:
            return None

        self.company_mock = LdapEntryMock(company_uuid)

        if company_uuid == 'company_with_contacts':
            self.company_mock.or_id = 'company_with_contacts'

        if company_uuid == 'company_with_technical_users':
            self.company_mock.or_id = 'company_with_technical_users'

        # assert self.company_mock().entry_dn.call_count == 1
        return self.company_mock

    def find_company(self, or_id):
        company_uuid = f'some_uuid_belonging_to_{or_id}'
        self.company_mock = LdapEntryMock(company_uuid)
        return self.company_mock
