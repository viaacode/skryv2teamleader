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
LDAP_PEOPLE_PREFIX = 'ou=users'
LDAP_ORGS_PREFIX = 'ou=apps,ou=users'
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

    def search(
            self,
            connection,
            search_base: str,
            filter: str = '(objectClass=*)',
            level=ldap3.SUBTREE,
            pagesize=DEFAULT_PAGE_SIZE):

        cookie = True
        while cookie:
            result = connection.search(
                search_base,
                filter,
                search_scope=level,
                attributes=self.search_attributes,
                time_limit=5,
                paged_size=pagesize,
                paged_criticality=True,
                paged_cookie=None if cookie is True else cookie,
            )
            if not isinstance(result, bool):
                response, result = connection.get_response(result)
            else:
                result = connection.result

            yield connection.entries

            try:
                cookie = result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            except KeyError:
                cookie = None

    def add(self, connection, dn: str, object_class=None, attributes=None):
        return connection.add(dn, object_class, attributes)

    def delete(self, connection, dn: str):
        return connection.delete(dn)


class LdapClient:
    """Acts as a client to query relevant information from LDAP"""

    def __init__(self, app_config: dict):
        params = app_config['ldap']
        app_env = app_config.get('environment', 'qas').lower()
        self.LDAP_SUFFIX = f"dc={app_env},dc=viaa,dc=be"
        print(f"LDAP_SUFFIX={self.LDAP_SUFFIX}")
        self.ldap_wrapper = LdapWrapper(params, SEARCH_ATTRIBUTES)

    def connection(self):
        return self.ldap_wrapper.connect()

    def _search(self, conn, prefix: str, partial_filter: str,
                modified_at: datetime = None, level=ldap3.SUBTREE, objectClass='*') -> list:
        # Format modify timestamp to an LDAP filter string
        modify_filter_string = (
            ''
            if modified_at is None
            else '(!(modifyTimestamp<={}))'.format(
                modified_at.astimezone(timezone.utc).strftime("%Y%m%d%H%M%SZ")
            )
        )
        # Construct the LDAP filter string
        filter = f'(&(objectClass={objectClass}){partial_filter}{modify_filter_string})'
        return self.ldap_wrapper.search(
            conn,
            f'{prefix},{self.LDAP_SUFFIX}',
            filter,
            level
        )

    def find_company_by_uuid(self, company_uuid):
        conn = self.connection()
        conn.search(
            search_base=f"ou=apps,ou=users,{self.LDAP_SUFFIX}",
            search_filter=f'(&(x-be-viaa-externalUUID={company_uuid})(structuralObjectClass=organization))',
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES]
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
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES]
        )

        if len(conn.entries) == 1:
            return conn.entries[0]
        elif len(conn.entries) > 1:
            # this shouldnt happen but if it does, we want it logged
            print("WARNING multiple companies found:", conn.entries, flush=True)
            return conn.entries[0]
        else:
            return None
