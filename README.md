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
plugins: asyncio-0.18.3, requests-mock-1.9.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 54 items                                                            

tests/test_app.py .......                                               [ 12%]
tests/test_app_startup.py .                                             [ 14%]
tests/unit/test_auth_tokens.py .                                        [ 16%]
tests/unit/test_document_service.py .....                               [ 25%]
tests/unit/test_milestone_service.py ............                       [ 48%]
tests/unit/test_process_service.py .....                                [ 57%]
tests/unit/test_scheduler.py ..                                         [ 61%]
tests/unit/test_slack_messages.py .....                                 [ 70%]
tests/unit/test_teamleader_client.py ................                   [100%]

============================= 54 passed in 1.98s ==============================
```

Run tests and get code coverage:
```
$ make coverage

============================= test session starts =============================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, requests-mock-1.9.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 88 items                                                            

tests/test_app.py ........                                              [  9%]
tests/test_app_startup.py .                                             [ 10%]
tests/unit/test_auth_tokens.py ..                                       [ 12%]
tests/unit/test_document_service.py .....                               [ 18%]
tests/unit/test_ldap_client.py .......                                  [ 26%]
tests/unit/test_milestone_service.py .................                  [ 45%]
tests/unit/test_process_service.py ..........                           [ 56%]
tests/unit/test_redis_cache.py .....                                    [ 62%]
tests/unit/test_scheduler.py ..                                         [ 64%]
tests/unit/test_skryv_base_service.py ......                            [ 71%]
tests/unit/test_slack_messages.py .....                                 [ 77%]
tests/unit/test_teamleader_client.py ....................               [100%]

---------- coverage: platform darwin, python 3.9.11-final-0 ----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
app/__init__.py                         0      0   100%
app/api/__init__.py                     0      0   100%
app/api/api.py                          6      0   100%
app/api/routers/__init__.py             0      0   100%
app/api/routers/health.py               9      0   100%
app/api/routers/skryv.py               18      0   100%
app/api/routers/webhook.py              6      0   100%
app/app.py                             38      0   100%
app/clients/__init__.py                 0      0   100%
app/clients/common_clients.py          15      0   100%
app/clients/ldap_client.py             41      0   100%
app/clients/redis_cache.py             32      0   100%
app/clients/skryv_client.py             6      0   100%
app/clients/slack_client.py            56      0   100%
app/clients/teamleader_auth.py         26      0   100%
app/clients/teamleader_client.py      188      8    96%
app/comm/__init__.py                    0      0   100%
app/comm/webhook_scheduler.py          45      0   100%
app/models/__init__.py                  0      0   100%
app/models/document.py                 17      0   100%
app/models/document_body.py             9      0   100%
app/models/document_value.py            3      0   100%
app/models/dossier.py                  15      0   100%
app/models/milestone.py                 9      0   100%
app/models/milestone_body.py            9      0   100%
app/models/process.py                  10      0   100%
app/models/process_body.py              9      0   100%
app/server.py                          24      0   100%
app/services/__init__.py                0      0   100%
app/services/document_service.py       31      0   100%
app/services/milestone_service.py     336      1    99%
app/services/process_service.py        98      0   100%
app/services/skryv_base.py             77      0   100%
app/services/webhook_service.py         6      0   100%
-------------------------------------------------------
TOTAL                                1139      9    99%
Coverage HTML written to dir htmlcov

============================= 88 passed in 3.70s ==============================
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
  LDAP_BIND: 'cn=root,dc=qas,dc=viaa,dc=be'
  LDAP_URI: 'ldaps://ldap-master-qas.do.viaa.be'
  SKRYV_DOSSIER_CP_ID: 90d24d34-b5b3-4942-8504-b6d76dd86ccb
  SLACK_CHANNEL: '#skryvbot'
  TL_API_URI: 'https://api.teamleader.eu'
  TL_AUTH_URI: 'https://app.teamleader.eu'
  TL_BESTELBON: fb842ba5-5372-0767-8752-e579d2e305b4
  TL_BT_AG: 2428da7f-3a95-0e60-9027-830116d5b69e
  TL_BT_BVBA: 9891b569-83d3-0da4-bd17-6776fa26aca4
  TL_BT_COMMV: 403342a8-5fc7-099d-a411-e6786fbba258
  TL_BT_COMMVA: 64b2e689-164b-0ac8-ae17-b4c31a103909
  TL_BT_CVBA: eb3a48bf-ec4d-0cb9-851c-0f7f586e5a9b
  TL_BT_CVOA: eb523036-88a1-04f0-9310-072187fe563a
  TL_BT_EBVBA: 3e6e790a-0c0c-008b-8b15-bc7d307c8716
  TL_BT_EENMANSZAAK: b745a4c5-05dd-0f6c-a713-50fd3f9adbe5
  TL_BT_ESV: 2056a504-6105-0a85-b11a-d16e3b5e36fe
  TL_BT_LV: 8811dacc-e557-01bc-8220-0407622203af
  TL_BT_NV: fa4f4d7f-c865-0ee6-b11f-0ed6a1e54fa2
  TL_BT_SBVBA: 1e9d421d-2799-0a55-ba1d-57a29a91e5a7
  TL_BT_SE: e2667f0b-4046-03d3-a52a-fadee6838267
  TL_BT_VERENIGIG: f73b93c8-5306-075a-9b17-3ebff19b94ed
  TL_BT_VOF: 2fa10c1a-fc5a-0597-8a18-8a17ab71266c
  TL_BT_VZW: aa805430-31a3-0667-b213-167923d41c13
  TL_CPSTATUS: afe9268c-c6dd-0053-bc5d-d4da5e723daa
  TL_FACTURATIE_EMAIL: 15846b7e-104d-015f-8753-cb945d823db9
  TL_FUNCTIE_CATEGORY: 17348dda-11c7-0e35-855b-38a4e1123dd6
  TL_INTENTIEVERKLARING: bcf9ceba-a988-0fc6-805f-9e087ea23dac
  TL_OPSTARTFASE: 32053d1e-e1f6-0436-9f52-8a6ce7423db4
  TL_REDIRECT_URI: 'https://services-qas.viaa.be/skryv/oauth'
  TL_RELATIE_MEEMOO: d46ecfe6-4329-0573-a85b-9c7d27023dd7
  TL_SWO: 05cf38ba-2d6f-01fe-a85f-dd84aad23dae
  TL_SWO_ADDENDA: 30aa7f48-8915-0a13-8853-4c04fee6bb11
  TL_TOESTEMMING_STARTEN: 1d0cc259-4b07-01b8-aa5b-100344423db0
  TL_TYPE_ORGANISATIE: 2245baba-81b2-0872-b159-9c553d323da7
  WEBHOOK_URL: 'https://services-qas.viaa.be'N
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

