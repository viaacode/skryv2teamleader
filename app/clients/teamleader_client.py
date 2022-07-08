#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/teamleader_client.py
#
#   TeamleaderClient handles communication with the exposed
#   json api from Teamleader.
#
#   The secret code, token and refresh_token are stored in redis
#   Whenever a 401 response is returned we call the method
#   auth_token_refresh to refresh the tokens using our redis cache
#
#   When a token update flow fails, a link is generated in the logs to request a new secret.
#   This links needs to be pasted into a browser and will result in a
#   code response that allows us to refetch a valid refresh_token from scratch using a new
#   issued secret.
#

import requests
import time
import json
import urllib.parse

from datetime import datetime
from app.clients.teamleader_auth import TeamleaderAuth
from app.clients.redis_cache import RedisCache
from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class TeamleaderAuthError(Exception):
    """Raised when authentication fails"""
    pass


class TeamleaderClient:
    """Acts as a client to query relevant information from Teamleader API"""

    def __init__(self, app_config: dict, redis_cache: RedisCache = None):
        params = app_config['teamleader']

        # Avoid getting 429 Too Many Requests error
        self.RATE_LIMIT = 0.4

        self.auth_uri = params['auth_uri']
        self.api_uri = params['api_uri']
        self.client_id = params['client_id']
        self.client_secret = params['client_secret']
        self.secret_code_state = params['secret_code_state']
        self.webhook_url = app_config['skryv']['webhook_url']
        self.webhook_jwt = app_config['skryv']['webhook_jwt']
        self.redirect_uri = self.secure_route(params['redirect_uri'])
        self.redirect_uri_base = params['redirect_uri']

        self.token_store = TeamleaderAuth(params, redis_cache)

        if not self.token_store.tokens_available():
            self.code = params['code']
            self.token = params['auth_token']
            self.refresh_token = params['refresh_token']
            self.token_store.save(self.code, self.token, self.refresh_token)
        else:
            self.code, self.token, self.refresh_token = self.token_store.read()

    def oauth_check(self):
        try:
            result = self.list_custom_fields(page=1, page_size=1)
            logger.info("Teamleader authorization status = OK")
            return {
                'status': 'ok'
            }
        except TeamleaderAuthError:
            link = self.authcode_request_link()
            logger.warning(
                f"Teamleader authorization expired. Use refresh link: {link} to renew tokens"
            )
            return {
                'status': 'authorization expired',
                'authorization_refresh_link': link
            }

    def authcode_request_link(self):
        """ First request that results in a callback to redirect_uri that supplies a code
        for auth_token_request. We return a link to be opened in browser while the user
        is logged into teamleader. The user then needs to click 'Geef toegang' and this triggers
        a request to the 'redirect_uri' that is handled by our authcode_callback method.
        """
        jwt_params = {
            'jwtauth': self.webhook_jwt,
        }
        encoded_params = urllib.parse.urlencode(jwt_params)
        redirect_uri = f"{self.redirect_uri_base}?{encoded_params}"

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': self.secret_code_state
        }

        encoded_params = urllib.parse.urlencode(params)
        link = f'{self.auth_uri}/oauth2/authorize?{encoded_params}'

        return link

    def auth_token_request(self):
        """ use when auth_token_refresh fails """
        req_uri = self.auth_uri + '/oauth2/access_token'
        req_params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': self.code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        r = requests.post(req_uri, data=req_params)
        time.sleep(self.RATE_LIMIT)
        self.handle_token_response(r)

    def handle_token_response(self, token_response):
        if token_response.status_code == 200:
            response = token_response.json()
            self.token = response['access_token']  # expires in 1 hour
            self.refresh_token = response['refresh_token']
            self.token_store.save(self.code, self.token, self.refresh_token)
        else:
            raise TeamleaderAuthError(token_response.text)

    def authcode_callback(self, code, state):
        """
        After user follows the authcode_request_link from above. we handle
        the callback here, and update our tokens.
        called with api route: /sync/oauth?code='supplied_by_teamleader'&state='self.secret_code_state'
        """
        if state != self.secret_code_state:
            logger.warning(
                "reject state={state} not equal to secret_state={self.secret_code_state}"
            )
            return {'status': 'code rejected'}

        try:
            self.code = code
            self.auth_token_request()
            return {'status': 'code accepted'}

        except TeamleaderAuthError as e:
            return {'error': f'code rejected: {str(e)}'}

    def auth_token_refresh(self):
        """ to be called whenever we get 401 from expiry on api calls """
        r = requests.post(
            self.auth_uri + '/oauth2/access_token',
            data={
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'refresh_token'
            }
        )
        time.sleep(self.RATE_LIMIT)
        self.handle_token_response(r)

    def request_endpoint(self, resource_path, params={}, headers={}):
        path = self.api_uri + resource_path
        headers['Authorization'] = "Bearer {}".format(self.token)
        res = requests.get(path, params=params, headers=headers)

        if res.status_code == 401:
            self.auth_token_refresh()
            headers = {'Authorization': "Bearer {}".format(self.token)}
            res = requests.get(path, params=params, headers=headers)

        time.sleep(self.RATE_LIMIT)

        if res.status_code == 200:
            return res.json()['data']
        else:
            error_msg = 'GET {} failed:\n status={}\n response={}\n params={}\n'.format(
                path,
                res.status_code,
                res.text,
                params
            )
            if res.status_code == 401:
                raise TeamleaderAuthError(error_msg)
            else:
                raise ValueError(error_msg)

    def request_page(self, resource_path, page=None, page_size=None, updated_since: datetime = None):
        params = {}
        if page:
            params['page[number]'] = page

        if page_size:
            params['page[size]'] = page_size

        if updated_since:
            # needs to be isormat without microsecond ex: '2021-03-29T16:44:33+00:00'
            params['filter[updated_since]'] = updated_since.replace(
                microsecond=0).isoformat()

        return self.request_endpoint(resource_path, params)

    def request_item(self, resource_path, resource_id):
        path = self.api_uri + resource_path
        headers = {'Authorization': "Bearer {}".format(self.token)}
        params = {}
        params['id'] = resource_id

        res = requests.get(path, params=params, headers=headers)
        if res.status_code == 401:
            self.auth_token_refresh()
            headers = {'Authorization': "Bearer {}".format(self.token)}
            res = requests.get(path, params=params, headers=headers)

        time.sleep(self.RATE_LIMIT)

        if res.status_code == 200:
            return res.json()['data']
        elif res.status_code == 404:
            logger.warning(f"Warning: {path} responded with {res.text}")
            return []
        else:
            error_msg = 'GET {} failed:\n status={}\n response={}\n'.format(
                path,
                res.status_code,
                res.text
            )
            raise ValueError(error_msg)

    def post_item(self, resource_path, payload):
        path = self.api_uri + resource_path
        headers = {
            'Authorization': "Bearer {}".format(self.token),
            'Content-type': 'application/json'
        }

        res = requests.post(path, data=json.dumps(payload), headers=headers)
        if res.status_code == 401:
            self.auth_token_refresh()
            headers = {
                'Authorization': "Bearer {}".format(self.token),
                'Content-type': 'application/json'
            }
            res = requests.post(
                path, data=json.dumps(payload), headers=headers)

        time.sleep(self.RATE_LIMIT)

        if res.status_code == 200 or res.status_code == 201:
            return res.json()['data']
        elif res.status_code == 204:
            return None
        else:
            error_msg = 'POST {} failed:\n status={}\n response={}\n'.format(
                path,
                res.status_code,
                res.text
            )
            raise ValueError(error_msg)

    def prepare_custom_fields(self, resource):
        custom_fields = resource['custom_fields']
        update_fields = []
        for f in custom_fields:
            if 'definition' in f:
                update_field = {}
                update_field['id'] = f['definition']['id']
                update_field['value'] = f['value']
                update_fields.append(update_field)

            if 'id' in f:
                update_fields.append(f)

        resource['custom_fields'] = update_fields

        return resource

    def list_companies(self, page=1, page_size=20, updated_since: datetime = None):
        return self.request_page(
            '/companies.list',
            page, page_size,
            updated_since
        )

    def get_company(self, uid):
        return self.request_item('/companies.info', uid)

    def update_company(self, company):
        company = self.prepare_custom_fields(company)
        result = self.post_item('/companies.update', company)
        return result

    def list_contacts(self, page=1, page_size=20, updated_since: datetime = None):
        return self.request_page(
            '/contacts.list',
            page, page_size,
            updated_since
        )

    def linked_contacts(self, company_id, page=1, page_size=20):
        params = {}
        params['filter[company_id]'] = company_id
        params['page[number]'] = page
        params['page[size]'] = page_size

        return self.request_endpoint('/contacts.list', params)

    def company_contacts(self, company_id):
        # get all linked contact details by iterating pages
        contacts = []
        page_size = 20
        page = 1
        while True:
            lc = self.linked_contacts(company_id, page, page_size)
            page += 1
            for c in lc:
                contacts.append(self.get_contact(c['id']))

            if len(lc) < page_size:
                break

        return contacts

    def get_contact(self, uid):
        return self.request_item('/contacts.info', uid)

    def update_contact(self, contact):
        contact = self.prepare_custom_fields(contact)
        return self.post_item('/contacts.update', contact)

    def add_contact(self, contact):
        return self.post_item('/contacts.add', contact)

    def link_to_company(self, contact_link):
        # contact_link == {'id':contact_id, 'company_id':...,
        #                  'position': 'ceo', 'decision_maker': true }
        return self.post_item('/contacts.linkToCompany', contact_link)

    def update_company_link(self, contact_link):
        return self.post_item('/contacts.updateCompanyLink', contact_link)

    def delete_contact(self, contact_id):
        return self.post_item('/contacts.delete', {'id': contact_id})

    def list_custom_fields(self, page=1, page_size=50):
        return self.request_page(
            '/customFieldDefinitions.list',
            page, page_size
        )

    def list_business_types(self, page=1, page_size=50):
        return self.request_page(
            '/businessTypes.list',
            page, page_size
        )

    def get_custom_field(self, uid):
        return self.request_item('/customFieldDefinitions.info', uid)

    def secure_route(self, url):
        if self.webhook_jwt and len(self.webhook_jwt) > 0:
            return f"{url}?jwtauth={self.webhook_jwt}"
        else:
            return url

    def get_migrate_uuid(self, resource_type, old_external_id):
        """resource_type == 'company', 'contact', ..."""
        path = self.api_uri + '/migrate.id'
        headers = {'Authorization': "Bearer {}".format(self.token)}
        params = {}
        params['id'] = old_external_id
        params['type'] = resource_type  # 'contact', 'company'

        res = requests.get(path, params=params, headers=headers)
        if res.status_code == 401:
            self.auth_token_refresh()
            headers = {'Authorization': "Bearer {}".format(self.token)}
            res = requests.get(path, params=params, headers=headers)

        time.sleep(self.RATE_LIMIT)

        if res.status_code == 200:
            return res.json()['data']['id']
        else:
            logger.error('call to {} failed\n error code={}\n error response {}\n used params {}\n'.format(
                path,
                res.status_code,
                res.text,
                params
            ))
            return None
