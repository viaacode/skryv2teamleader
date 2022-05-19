#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/webhook_service.py
#
#   WebhookService handles listing, creating and deleting all webhooks
#


class WebhookService:

    def __init__(self, teamleader_client):
        self.tlc = teamleader_client

    def list_webhooks(self):
        return {
            'registered_webhooks': self.tlc.list_webhooks(),
            'webhook_url': self.tlc.webhook_url
        }

    def update_webhooks(self):
        # unregister all old existing webhooks and re-install new ones
        # we us list_webhooks because most likely token is changed now
        existing_webhooks = self.tlc.list_webhooks()
        for hook in existing_webhooks:
            for hook_type in hook['types']:
                self.tlc.unregister_webhook(hook['url'], hook_type, True)

        self.create_webhooks()
        return {'status': f'webhooks to {self.tlc.webhook_url} updated'}

    def create_webhooks(self):
        # add company webhooks
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/company/create', 'company.added')
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/company/update', 'company.updated')
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/company/delete', 'company.deleted')

        # add contact webhooks
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/contact/update', 'contact.updated')
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/related_contacts/update', 'contact.linkedToCompany')
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/related_contacts/update', 'contact.unlinkedFromCompany')
        self.tlc.register_webhook(
            f'{self.tlc.webhook_url}/ldap/contact/delete', 'contact.deleted')

        return {'status': f'webhooks to {self.tlc.webhook_url} created'}

    def delete_webhooks(self):
        # remove company webhooks
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/company/create', 'company.added')
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/company/update', 'company.updated')
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/company/delete', 'company.deleted')

        # remove contact webhooks
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/contact/update', 'contact.updated')
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/related_contacts/update', 'contact.linkedToCompany')
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/related_contacts/update', 'contact.unlinkedFromCompany')
        self.tlc.unregister_webhook(
            f'{self.tlc.webhook_url}/ldap/contact/delete', 'contact.deleted')

        return {'status': f'webhooks to {self.tlc.webhook_url} deleted'}
