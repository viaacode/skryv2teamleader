#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_ldap_client.py
#

import pytest
import uuid
from unittest.mock import patch, MagicMock

from app.clients.ldap_client import LdapClient
from testing_config import tst_app_config
from ldap3.core.exceptions import LDAPSocketOpenError


class MockLdap():
    def __init__(self):
        self.entries = ['some ldap entry']

    def search(self, search_base, search_filter, attributes):
        if 'plural' in search_filter:
            self.entries = ['first entry', 'b', 'c']

        if 'unknown' in search_filter:
            self.entries = []


def fake_ldap_connect():
    return MockLdap()


class TestLdapClient:
    @pytest.fixture
    def ldap(self):
        ldap_client = LdapClient(tst_app_config())
        return ldap_client

    def test_find_company_by_uuid(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company_by_uuid('some_uuid')
            assert c == 'some ldap entry'

    def test_find_company_by_uuid_multiple(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company_by_uuid('some_plural_uuid')
            assert c == 'first entry'

    def test_find_company_by_uuid_unknown(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company_by_uuid('unknown_uuid')
            assert c is None

    def test_find_company(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company('OR-testing')
            assert c == 'some ldap entry'

    def test_find_company_multiple(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company('some_plural_uuid')
            assert c == 'first entry'

    def test_find_company_unknown(self, ldap):
        with patch.object(ldap, 'connection', MagicMock(side_effect=fake_ldap_connect)) as mocked_connect:
            c = ldap.find_company('unknown_uuid')
            assert c is None

    def test_connection_raises_on_test_adress(self, ldap):
        with pytest.raises(LDAPSocketOpenError):
            c = ldap.find_company('test_connection')
            assert c is None
