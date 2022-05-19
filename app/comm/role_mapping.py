#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/comm/role_mapping.py
#
#  This maps ldap memberOf value into Teamleader roles custom field
#  Used in ContactService
#
#    example:
#
#     ldap memberOf : ['cn=mediahaven,ou=apps,ou=groups,dc=qas,dc=viaa,dc=be',
#                      'cn=cataloguspro,ou=apps,ou=groups,dc=qas,dc=viaa,dc=be']
#     maps to 'value': ['gebruiker MAM', 'gebruiker Catalogus Pro']


class RoleMapping:
    @staticmethod
    def ldap_role_to_teamleader(ldap_member):
        try:
            # remove 'cn=' and 'ou=...' from the ldap_member string
            role = ldap_member.split(',')[0].split('cn=')[1]
        except IndexError:
            print(
                "warning index error in role mapping role={role}", flush=True)
            return None

        rolesmap = {
            "inventaris": "gebruiker inventaristool",
            "amsweb": "gebruiker AMS",
            "mediahaven": "gebruiker MAM",
            "ftp": "gebruiker ftp",
            "cataloguspro": "gebruiker Catalogus Pro",
            "skryvweb": "gebruiker contract.meemoo.be",
            "hetarchief-beheer": "hetarchief beheer",
            # these are also possible in ldap server but not in custom_fields yet:
            # "gw_api": "gebruiker gw api",
            # "ldap_api": "gebruiker LDAP API",
            # "organization_api": "gebruiker Organization API",
            # "skryv_api": "gebruiker skryv api",
            # "pwmadmin": "pwm administrator"
        }

        # TODO :if we detect for instance the value does not match
        # but is close 'gebruiker Ams' instead of 'gebruiker AMS' -> make
        # zendesk message explaining there is now an issue because someone edited custom fields
        # and did not update this mapping.
        # also this map and the SectorMapping will have to be maintained and we will most likely
        # need to put this in a central config file which can be customized with env vars.

        return rolesmap.get(role, None)

    @staticmethod
    def convert(ldap_member_of):
        tl_roles = []

        # handle case were single role is returned as string by ldap
        if isinstance(ldap_member_of, str):
            tl_role = RoleMapping.ldap_role_to_teamleader(ldap_member_of)
            if tl_role is not None:
                tl_roles.append(tl_role)

            return tl_roles

        for m in ldap_member_of:
            tl_role = RoleMapping.ldap_role_to_teamleader(m)
            if tl_role is not None:
                tl_roles.append(tl_role)

        return tl_roles
