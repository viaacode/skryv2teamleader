from fastapi.testclient import TestClient
import pytest

from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.common_clients import CommonClients
from app.clients.teamleader_client import TeamleaderClient

from tests.unit.mock_teamleader_client import MockTlClient
from tests.unit.mock_ldap_client import MockLdapClient
from tests.unit.mock_redis_cache import MockRedisCache
from tests.unit.testing_config import tst_app_config


@pytest.fixture
def slack(mocker):
    app_config = tst_app_config()
    app_config["environment"] = "QAS"
    mocked_client = SlackClient(app_config)
    mocker.patch.object(
        mocked_client,
        "_post_to_webhook",
        autospec=True,
        return_value=None,
    )
    mocker.spy(
        mocked_client,
        "create_message",
    )
    return mocked_client


@pytest.fixture
def app_client(mock_clients):
    from app.server import app
    from app.server import main_app

    main_app.redis_cache = MockRedisCache()
    main_app.start_clients(False)
    main_app.clients = mock_clients
    return TestClient(app)


@pytest.fixture
def mock_clients(slack):
    return CommonClients(
        MockTlClient(),
        MockLdapClient(),
        slack,
        SkryvClient(tst_app_config()),
        MockRedisCache(),
    )


@pytest.fixture
def mock_client_requests(slack):
    tlc = TeamleaderClient(
        tst_app_config(),
        MockRedisCache(),
    )
    # switch off rate limiting for fast tests
    tlc.RATE_LIMIT = 0.0

    return CommonClients(
        tlc,
        MockLdapClient(),
        slack,
        SkryvClient(tst_app_config()),
        MockRedisCache(),
    )
