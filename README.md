# Skryv2Teamleader

Receive webhook calls from Skryv meemoo and make updates in teamleader.
We handle proces, milestone and document calls.

# Installing
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

# Testing

```
$ make test
============================= test session starts =============================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 24 items                                                            

tests/test_app.py ..........                                            [ 41%]
tests/unit/test_auth_tokens.py .                                        [ 45%]
tests/unit/test_scheduler.py .............                              [100%]

============================= 24 passed in 1.05s ==============================
```

Also get testing code coverage:
```
$ make coverage
============================= test session starts =============================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 25 items                                                            

tests/test_app.py ..........                                            [ 40%]
tests/unit/test_auth_tokens.py .                                        [ 44%]
tests/unit/test_scheduler.py ..............                             [100%]

---------- coverage: platform darwin, python 3.9.11-final-0 ----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
app/__init__.py                         0      0   100%
app/api/__init__.py                     0      0   100%
app/api/api.py                          6      0   100%
app/api/routers/__init__.py             0      0   100%
app/api/routers/health.py               5      0   100%
app/api/routers/skryv.py               19      0   100%
app/api/routers/webhook.py             45      3    93%
app/app.py                             45      1    98%
app/clients/__init__.py                 0      0   100%
app/clients/common_clients.py          13      0   100%
app/clients/ldap_client.py             37     18    51%
app/clients/redis_cache.py             30      5    83%
app/clients/skryv_client.py             9      0   100%
app/clients/slack_client.py            37     16    57%
app/clients/teamleader_auth.py         22      1    95%
app/clients/teamleader_client.py      222    156    30%
app/comm/__init__.py                    0      0   100%
app/comm/webhook_scheduler.py          45      4    91%
app/models/__init__.py                  0      0   100%
app/models/document.py                 17      0   100%
app/models/document_body.py             9      0   100%
app/models/document_value.py            3      0   100%
app/.py                  15      0   100%
app/models/milestone.py                 9      0   100%
app/models/milestone_body.py            9      0   100%
app/models/process.py                  10      0   100%
app/models/process_body.py              9      0   100%
app/server.py                          25      7    72%
app/services/__init__.py                0      0   100%
app/services/document_service.py       49      3    94%
app/services/milestone_service.py      31      3    90%
app/services/process_service.py        62      5    92%
app/services/skryv_base.py             49      5    90%
app/services/webhook_service.py        22      0   100%
ldap_cli.py                            17     17     0%
-------------------------------------------------------
TOTAL                                 871    244    72%
Coverage HTML written to dir htmlcov

============================= 25 passed in 2.12s ==============================
```

