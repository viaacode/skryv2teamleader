def tst_app_config():
    return {
        'environment': 'TST',
        'slack': {
            'token': 'test_token',
            'channel': 'test_channel',
        },
        'teamleader': {
            'auth_uri': 'https://app.teamleader.eu',
            'api_uri': 'https://api.teamleader.eu',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'secret_code_state': 'test_secret_code_state',
            'code': 'test_teamleader_code',
            'auth_token': 'test_teamleader_auth_token',
            'refresh_token': 'test_teamleader_refresh_token',
            'redirect_uri': 'https://services-qas.testing.com',
            'redis': 'redis://localhost:6543'
        },
        'skryv': {
            'webhook_url': 'http://localhost:8080',
            'webhook_jwt': 'some_jwt_here_to_secure_route'
        }
    }
