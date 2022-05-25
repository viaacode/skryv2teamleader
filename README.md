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
================================= test session starts ==================================
platform darwin -- Python 3.9.11, pytest-7.1.2, pluggy-1.0.0 -- /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader/python_env/bin/python
cachedir: .pytest_cache
rootdir: /Users/wschrep/FreelanceWork/Meemoo/skryv2teamleader, configfile: pytest.ini
plugins: asyncio-0.18.3, cov-2.8.1, mock-3.5.1
asyncio: mode=auto
collected 14 items                                                                     

tests/test_app.py::TestAppRequests::test_webhook_delete PASSED                   [  7%]
tests/test_app.py::TestAppRequests::test_webhook_list PASSED                     [ 14%]
tests/test_app.py::TestAppRequests::test_webhook_create PASSED                   [ 21%]
tests/test_app.py::TestAppRequests::test_health PASSED                           [ 28%]
tests/test_app.py::TestAppRequests::test_oauth_rejection PASSED                  [ 35%]
tests/test_app.py::TestAppRequests::test_oauth_bad_code PASSED                   [ 42%]
tests/test_app.py::TestAppRequests::test_milestone_events PASSED                 [ 50%]
tests/test_app.py::TestAppRequests::test_process_events PASSED                   [ 57%]
tests/test_app.py::TestAppRequests::test_document_events PASSED                  [ 64%]
tests/unit/test_scheduler.py::TestScheduler::test_process_created_event PASSED   [ 71%]
tests/unit/test_scheduler.py::TestScheduler::test_milestone_akkoord PASSED       [ 78%]
tests/unit/test_scheduler.py::TestScheduler::test_document_update PASSED         [ 85%]
tests/unit/test_scheduler.py::TestScheduler::test_invalid_webhook PASSED         [ 92%]
tests/unit/test_scheduler.py::TestScheduler::test_scheduling PASSED              [100%]

================================== 14 passed in 1.07s ==================================
```
