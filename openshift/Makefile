.ONESHELL:
SHELL = /bin/sh

.PHONY: all test

test:
	apk add --no-cache gcc musl-dev
	pip install -r requirements.txt --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple --trusted-host do-prd-mvn-01.do.viaa.be
	pip install -r requirements-test.txt
	export $(shell cat .env.example | xargs)
	python -m pytest -vvv --cov=./app --junit-xml=./tests/test_results.xml