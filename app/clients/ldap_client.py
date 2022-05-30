#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Authors: original: Mattias Poppe, Rudolf Degeijter, extended by: Walter Schreppers
#
#   app/clients/ldap_client.py
#
#  This is only needed to lookup the or-id and map to a teamleader uuid for updates
#

import ldap3
from datetime import datetime, timezone

DEFAULT_PAGE_SIZE = 200
# LDAP_PEOPLE_PREFIX = 'ou=users'
# LDAP_ORGS_PREFIX = 'ou=apps,ou=users'
SEARCH_ATTRIBUTES = [
    ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES
]


class LdapWrapper:
    """Allows for communicating with an LDAP server"""

    def __init__(self, params: dict, search_attributes=ldap3.ALL_ATTRIBUTES,
                 get_info=ldap3.SCHEMA, client_strategy=ldap3.SYNC):

        self.search_attributes = search_attributes
        self.user = params.get('bind')
        self.password = params.get('password')
        self.server = ldap3.Server(params['URI'], get_info=get_info)
        self.client_strategy = client_strategy

    def connect(self):
        return ldap3.Connection(
            self.server, self.user, self.password,
            client_strategy=self.client_strategy,
            auto_bind=True
        )


class LdapClient:
    """Acts as a client to query relevant information from LDAP"""

    def __init__(self, app_config: dict):
        params = app_config['ldap']
        app_env = app_config.get('environment', 'qas').lower()
        self.LDAP_SUFFIX = f"dc={app_env},dc=viaa,dc=be"
        self.ldap_wrapper = LdapWrapper(params, SEARCH_ATTRIBUTES)

    def connection(self):
        return self.ldap_wrapper.connect()

    def find_company_by_uuid(self, company_uuid):
        conn = self.connection()
        conn.search(
            search_base=f"ou=apps,ou=users,{self.LDAP_SUFFIX}",
            search_filter=f'(&(x-be-viaa-externalUUID={company_uuid})(structuralObjectClass=organization))',
            attributes=SEARCH_ATTRIBUTES
        )

        if len(conn.entries) == 1:
            return conn.entries[0]
        elif len(conn.entries) > 1:
            # this shouldnt happen but if it does, we want it logged
            print("WARNING multiple companies found:", conn.entries, flush=True)
            return conn.entries[0]
        else:
            return None

    def find_company(self, or_id):
        conn = self.connection()
        conn.search(
            search_base=f"ou=apps,ou=users,{self.LDAP_SUFFIX}",
            search_filter=f'(&(o={or_id})(structuralObjectClass=organization))',
            attributes=SEARCH_ATTRIBUTES
        )

        if len(conn.entries) == 1:
            return conn.entries[0]
        elif len(conn.entries) > 1:
            # this shouldnt happen but if it does, we want it logged
            print("WARNING multiple companies found:", conn.entries, flush=True)
            return conn.entries[0]
        else:
            return None
