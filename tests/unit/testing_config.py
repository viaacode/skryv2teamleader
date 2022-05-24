def tst_app_config():
    return {
        'slack': {
            'token': 'test_token',
            'channel': 'test_channel',
        },
        'environment': 'TST',
        'teamleader': {
            'webhook_url': 'http://testing_webhook_url'
        }
    }
