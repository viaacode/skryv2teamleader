#  @Author: Walter Schreppers
#
#  tests/test_app.py
#
#   This tests the main fast-api calls provided
#
#   We mock the response from teamleader
#

import pytest
import json
import glob

# from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.clients.slack_client import SlackClient
from app.clients.common_clients import CommonClients

from tests.unit.mock_teamleader_client import MockTlClient
from tests.unit.mock_ldap_client import MockLdapClient
from tests.unit.mock_slack_wrapper import MockSlackWrapper
from tests.unit.testing_config import tst_app_config
from tests.unit.mock_redis_cache import MockRedisCache


class TestAppRequests:
    @pytest.fixture
    def app_client(self):
        from app.server import app
        from app.server import main_app
        main_app.redis_cache = MockRedisCache()
        main_app.start_clients(False)
        main_app.clients = self.mock_clients()
        return TestClient(app)

    def mock_clients(self):
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()

        return CommonClients(
            MockTlClient(),
            MockLdapClient(),
            slack_client,
            MockRedisCache()
        )

    def test_webhook_list(self, app_client):
        response = app_client.get("/webhooks/list")
        assert response.status_code == 200
        content = response.json()
        assert content['registered_webhooks'] == [
            'skryv_webhook_url/skryv/process',
            'skryv_webhook_url/skryv/document',
            'skryv_webhook_url/skryv/milestone',
        ]

    def test_health(self, app_client):
        response = app_client.get("/health/live")
        assert response.status_code == 200
        assert response.text == '"OK"'

    def test_oauth_rejection(self, app_client):
        response = app_client.get("/skryv/oauth")
        assert response.status_code == 422

    # TODO: test /sync/oauth get call (with correct code)
    def test_oauth_bad_code(self, app_client):
        response = app_client.get("/skryv/oauth?code=123")
        assert response.status_code == 200
        # assert response.json() == 'code rejected'

    def test_milestone_events(self, app_client):
        for milestone_fixture in glob.glob("tests/fixtures/milestone/*.json"):
            ms = open(milestone_fixture, "r")
            response = app_client.post(
                "/skryv/milestone",
                json=json.loads(ms.read())
            )
            ms.close()

            assert response.status_code == 200
            content = response.json()
            assert len(content['status']) > 0

    def test_process_events(self, app_client):
        for process_fixture in glob.glob("tests/fixtures/process/*.json"):
            proc = open(process_fixture, "r")
            response = app_client.post(
                "/skryv/process",
                json=json.loads(proc.read())
            )
            proc.close()

            assert response.status_code == 200
            content = response.json()
            assert 'proces event received' in content['status']

    def test_document_events(self, app_client):
        for document_fixture in glob.glob("tests/fixtures/document/*.json"):
            doc = open(document_fixture, "r")
            response = app_client.post(
                "/skryv/document",
                json=json.loads(doc.read())
            )
            doc.close()

            assert response.status_code == 200
            content = response.json()
            assert 'document event received' in content['status']
