#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/mock_or_id_generator.py
#
#     Mocks organization id request calls to microservice of herwig
#

from tests.unit.mock_client import MockClient


class MockOrgIdGenerator(MockClient):
    def __init__(self):
        super().__init__()

    def mocked_org_id(self):
        return 'OR-aabbcc1'

    def generate_called(self):
        return super().method_called('generate')

    def generate(self):
        super().method_call('generate: {self.mocked_org_id()}')
        return self.mocked_org_id()
