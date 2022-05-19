#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/org_id_generator.py
#
#   OrgIdGenerator generates new or-id's to create organizations in ldap
#   This uses an internal service from Herwig Bogaert on our vpn.
#   We call a route on a small microservice to get back an original or-id
#   for creating a new organization in ldap which is then saved as new company in teamleader
#

import requests


class OrgIdGenerator:
    def __init__(self, params):
        self.orgs_api_url = params['organizations']['or_id_url']

    def generate(self):
        result = requests.get(self.orgs_api_url)
        if result.status_code != 200:
            raise ValueError('Call to {self.orgs_api_url} failed.')

        new_or_id = result.text.split('id: ')[1].strip()
        if len(new_or_id) != 7:
            raise ValueError(
                'Generated or_id {new_or_id} is invalid, should be length=7'
            )

        return f'OR-{new_or_id}'
