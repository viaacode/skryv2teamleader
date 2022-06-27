# Skryv2Teamleader

Receive webhook calls from Skryv meemoo and make updates in teamleader.
We handle proces, milestone and document calls.
More documentation about the different incoming webhook calls implement can be found here:
https://meemoo.atlassian.net/wiki/spaces/IK/pages/818086103/contract.meemoo.be+en+Teamleader+skryv2teamleader


## Installing
Running make without args gives usage:
```
make
Available make commands for skryv2teamleader:

  install     install packages and prepare environment
  clean       remove all temporary files
  lint        run the code linters
  format      reformat code
  test        run all the tests
  dockertest  run all the tests in docker image like jenkins
  dockerrun   run docker image and serve api
  coverage    run tests and generate coverage report
  console     start python cli with env vars set
  server      start uvicorn development server fast-api for synchronizing with ldap
```

Just run make install to install packages.
and then start the server with make server:

To start the fast-api for skryv2teamleader just use the make server command:
```
$ make server
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [51089] using statreload
INFO:     Started server process [51091]
```

## Testing

```
$ make test
============================= test session starts =============================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 31 items                                                            

tests/test_app.py ..........                                            [ 32%]
tests/unit/test_auth_tokens.py .                                        [ 35%]
tests/unit/test_document_service.py .....                               [ 51%]
tests/unit/test_milestone_service.py .........                          [ 80%]
tests/unit/test_process_service.py ....                                 [ 93%]
tests/unit/test_scheduler.py ..                                         [100%]

============================= 31 passed in 1.21s ==============================
```

Run tests and get code coverage:
```
$ make coverage
============================= test session starts =============================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0
rootdir: Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 34 items                                                            

tests/test_app.py .......                                               [ 20%]
tests/test_app_startup.py .                                             [ 23%]
tests/unit/test_auth_tokens.py .                                        [ 26%]
tests/unit/test_document_service.py .....                               [ 41%]
tests/unit/test_milestone_service.py ..........                         [ 70%]
tests/unit/test_process_service.py .....                                [ 85%]
tests/unit/test_scheduler.py ..                                         [ 91%]
tests/unit/test_slack_messages.py ...                                   [100%]

---------- coverage: platform darwin, python 3.9.11-final-0 ----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
app/__init__.py                         0      0   100%
app/api/__init__.py                     0      0   100%
app/api/api.py                          6      0   100%
app/api/routers/__init__.py             0      0   100%
app/api/routers/health.py               5      0   100%
app/api/routers/skryv.py               19      0   100%
app/api/routers/webhook.py              6      0   100%
app/app.py                             36      0   100%
app/clients/__init__.py                 0      0   100%
app/clients/common_clients.py          15      0   100%
app/clients/ldap_client.py             41     18    56%
app/clients/redis_cache.py             32      7    78%
app/clients/skryv_client.py             6      0   100%
app/clients/slack_client.py            50      8    84%
app/clients/teamleader_auth.py         26      1    96%
app/clients/teamleader_client.py      177    120    32%
app/comm/__init__.py                    0      0   100%
app/comm/webhook_scheduler.py          45      4    91%
app/models/__init__.py                  0      0   100%
app/models/document.py                 17      0   100%
app/models/document_body.py             9      0   100%
app/models/document_value.py            3      0   100%
app/models/dossier.py                  15      0   100%
app/models/milestone.py                 9      0   100%
app/models/milestone_body.py            9      0   100%
app/models/process.py                  10      0   100%
app/models/process_body.py              9      0   100%
app/server.py                          25      1    96%
app/services/__init__.py                0      0   100%
app/services/document_service.py       31      1    97%
app/services/milestone_service.py     298     31    90%
app/services/process_service.py        94      9    90%
app/services/skryv_base.py             73      6    92%
app/services/webhook_service.py         6      0   100%
-------------------------------------------------------
TOTAL                                1072    206    81%
Coverage HTML written to dir htmlcov

============================= 34 passed in 2.29s ==============================
```

## Environment and configmap
There are some env vars that need to be set up. An example is given in .env.example

Example openshift configmap QAS, look op openshift for the production uuid configuration:
```
kind: ConfigMap
apiVersion: v1
metadata:
  name: skryv2teamleader-qas
  namespace: etl
  labels:
    app: skryv2teamleader
    app.kubernetes.io/component: skryv2teamleader-qas
    app.kubernetes.io/instance: skryv2teamleader-qas
    app.kubernetes.io/name: skryv2teamleader
    app.kubernetes.io/part-of: skryv2teamleader
    app.openshift.io/runtime: skryv2teamleader
    app.openshift.io/runtime-version: qas
    env: qas
data:
  ENVIRONMENT: QAS
  TL_AUTH_URI: https://app.teamleader.eu
  TL_API_URI: https://api.teamleader.eu
  TL_REDIRECT_URI: https://services-qas.viaa.be/ldap/oauth
  WEBHOOK_URL: https://services-qas.viaa.be/skryv
  LDAP_URI: ldaps://ldap-master-qas.do.viaa.be
  LDAP_BIND: "cn=root,..."
  SLACK_CHANNEL: "#crmbot"
  SKRYV_DOSSIER_CP_ID: 90d24d34-b5b3-4942-8504-b6d76dd86ccb
  TL_OPSTARTFASE: 32053d1e-e1f6-0436-9f52-8a6ce7423db4
  TL_CPSTATUS: afe9268c-c6dd-0053-bc5d-d4da5e723daa
  TL_INTENTIEVERKLARING: bcf9ceba-a988-0fc6-805f-9e087ea23dac
  TL_TOESTEMMING_STARTEN: 1d0cc259-4b07-01b8-aa5b-100344423db0
  TL_SWO: 05cf38ba-2d6f-01fe-a85f-dd84aad23dae
  TL_SWO_ADDENDA: 30aa7f48-8915-0a13-8853-4c04fee6bb11
  TL_TYPE_ORGANISATIE: 2245baba-81b2-0872-b159-9c553d323da7
  TL_FACTURATIE_EMAIL: 15846b7e-104d-015f-8753-cb945d823db9
  TL_BESTELBON: fb842ba5-5372-0767-8752-e579d2e305b4
  TL_RELATIE_MEEMOO: d46ecfe6-4329-0573-a85b-9c7d27023dd7
  TL_FUNCTIE_CATEGORY: 17348dda-11c7-0e35-855b-38a4e1123dd6
```


Example openshift secrets to set in a secrets map:
```
TL_CLIENT_ID=client_id_teamleader
TL_CLIENT_SECRET=secret_from_teamleader
TL_SECRET_CODE_STATE=qas_secret_state_some_key_here
TL_CODE=code_from_callback
TL_AUTH_TOKEN=teamleader_token
TL_REFRESH_TOKEN=teamleader_refresh_token
WEBHOOK_JWT=jwt_here
REDIS_URL=some_redis_url_here/db
LDAP_PASSWORD=ldap_password_here
SLACK_TOKEN=slack_token_here
```

