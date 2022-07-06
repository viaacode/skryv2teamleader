#  @Author: Walter Schreppers
#
#  tests/test_app_startup.py
#
#   This tests app/server.py startup+shutdown events
#   and that the root route shows the swagger docs

import pytest
from fastapi.testclient import TestClient
from app.server import app


class TestAppStartup:
    def test_root(self):
        with TestClient(app) as app_client_with_startup:
            response = app_client_with_startup.get("/")
            assert response.status_code == 200
            assert 'Skryv2Teamleader - Swagger UI' in response.text
