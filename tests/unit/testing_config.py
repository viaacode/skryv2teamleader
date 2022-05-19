def tst_app_config():
    return {
        'slack': {
            'token': 'test_token',
            'channel': 'test_channel',
        },
        'zendesk': {
            'email': 'test_email@example.com',
            'token': 'test_zendesk_token',
            'subdomain': 'test_zendesk_domain'
        },
        'environment': 'TST',
        'teamleader': {
            'webhook_url': 'http://testing_webhook_url'
        }
    }
