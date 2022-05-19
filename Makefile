NAME := skryv2teamleader
FOLDERS := ./app/ ./tests/

.DEFAULT_GOAL := help


.PHONY: help
help:
	@echo "Available make commands for $(NAME):"
	@echo ""
	@echo "  install     install packages and prepare environment"
	@echo "  clean       remove all temporary files"
	@echo "  lint        run the code linters"
	@echo "  format      reformat code"
	@echo "  test        run all the tests"
	@echo "  dockertest  run all the tests in docker image like jenkins"
	@echo "  dockerrun   run docker image and serve api"
	@echo "  coverage    run tests and generate coverage report"
	@echo "  console     start python cli with env vars set"
	@echo "  benchmark       start uvicorn production server for benchmark"
	@echo "  server      start uvicorn development server fast-api for synchronizing with ldap"
	@echo ""


.PHONY: install
install:
	mkdir -p python_env; \
	python3 -m venv python_env; \
	. python_env/bin/activate; \
	python3 -m pip install --upgrade pip; \
	python3 -m pip install -r requirements.txt; \
	python3 -m pip install -r requirements-test.txt


.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {}; \
	rm -rf .coverage htmlcov


.PHONY: lint
lint:
	@. python_env/bin/activate; \
	flake8 --max-line-length=120 --exclude=.git,python_env,__pycache__


.PHONY: format
format:
	@. python_env/bin/activate; \
	autopep8 --in-place -r app; \
	autopep8 --in-place -r tests;

.PHONY: test
test:
	@. python_env/bin/activate; \
	export `grep -v '^#' .env.example | xargs` && \
	python -m pytest -vv


.PHONY: dockertest
dockertest:
	docker build . -t teamleader2ldap; \
	docker container run --name teamleader2ldap --env-file .env.example --entrypoint python "teamleader2ldap" "-m" "pytest"

.PHONY: dockerrun
dockerrun:
	docker build . -t teamleader2ldap; \
	docker container run --name teamleader2ldap --env-file .env --entrypoint python "teamleader2ldap" "-m" "main"


.PHONY: coverage
coverage:
	@. python_env/bin/activate; \
	export `grep -v '^#' .env.example | xargs` && \
	python -m pytest --cov-config=.coveragerc --cov . .  --cov-report html --cov-report term


.PHONY: code_callback_example
code_callback_example:
	curl "http://localhost:8080/sync/oauth?code=CODE_HERE&state=qas_secret_state"


.PHONY: console
console:
	@. python_env/bin/activate; \
	export `grep -v '^#' .env | xargs` && \
	python


.PHONY: server
server:
	@. python_env/bin/activate; \
	export `grep -v '^#' .env | xargs` && \
	uvicorn app.server:app --reload --port 8080 --no-access-log --reload-dir app

.PHONY: benchmark
benchmark:
	@. python_env/bin/activate; \
	export `grep -v '^#' .env | xargs` && \
	python main.py

