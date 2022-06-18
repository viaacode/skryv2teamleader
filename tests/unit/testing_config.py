def tst_app_config():
    return {
        'slack': {
            'token': 'test_token',
            'channel': 'test_channel',
        },
        'environment': 'TST',
        'teamleader': {
            'redis': 'redis://localhost:6543'
        },
        'skryv':{
            'webhook_url': 'http://localhost:8080'
        }
    }
