# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

SHELL := /bin/bash

# bootstrap your dev env, do it for a clean environment
bootstrap: setup-env build-frontend


# setup a clean environment for development, only run this if you know what exactly
# you need.
# if your wanted a clean environment, always run `bootstrap` instead.
setup-env:
	-rm backend/.env
	-rm backend/.env-2
	-rm thirdparty/libra-reference-utils/external_services/liquidity/.env
	-rm thirdparty/libra-reference-utils/external_services/liquidity/.env-2
	scripts/lrw.sh setup_environment

# build frontend may take some time to run, but is required for `dev` target
build-frontend:
	scripts/lrw.sh build frontend


# clean all docker images, volumes
# TODO: only clean up docker stuff is created by LRW.
clean-docker:
	-docker kill $(shell docker ps -aq)
	-docker rm $(shell docker ps -aq)
	-docker volume rm $(shell docker volume ls -q)


# start local development, run `bootstrap` for a clean environment first.
# you may need run `build-frontend`.
dev: clean-docker
	./scripts/lrw.sh build
	./scripts/lrw.sh develop


.PHONY: bootstrap setup-env build-frontend clean-docker dev


# testing


test: format backend-test

alltests: test e2e

e2e: clean-docker build-e2e single double
dtest: clean-docker build-e2e double


# build e2e double test images and setup env variables
build-e2e:
	./scripts/lrw.sh build 8080 e2e


# run e2e single test
single:
	./scripts/lrw.sh e2e single up > single.vars
	# 7 services should have log, 1 gateway has no log
	./scripts/wait_for_server_ready.sh 6
	cat single.vars
	source single.vars && ./scripts/test_e2e.sh single

# run e2e double test
double:
	./scripts/lrw.sh e2e double up > double.vars
	# 14 services should have log, 2 gateways has no log
	./scripts/wait_for_server_ready.sh 12
	cat double.vars
	source double.vars && ./scripts/test_e2e.sh double


.PHONY: test alltests e2e build-e2e single double

# backend testing

pyre:
	PIPENV_PIPFILE=backend/Pipfile pipenv run pyre --search-path \
		"$(shell PIPENV_PIPFILE=backend/Pipfile pipenv --venv)/lib/python3.7/site-packages/" \
		check


check:
	PIPENV_PIPFILE=backend/Pipfile pipenv run black --check backend


format:
	PIPENV_PIPFILE=backend/Pipfile pipenv run black backend


backend-install:
	PIPENV_PIPFILE=backend/Pipfile pipenv run python3 backend/setup.py develop


backend-test: backend-install
	PIPENV_PIPFILE=backend/Pipfile pipenv run pytest \
		--ignore=backend/tests/e2e_tests backend/tests -k "$(T)" -W ignore::DeprecationWarning


.PHONY: pyre check format backend-install backend-test
