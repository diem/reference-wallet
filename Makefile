# Copyright (c) The Diem Core Contributors
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
	-rm liquidity/.env
	-rm liquidity/.env-2
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

alltest: test e2e

e2e: clean-docker build-e2e double-env e2e-test

# build e2e test images
build-e2e:
	./scripts/lrw.sh build 8080 e2e

# setup e2e tests environment variables
double-env:
	./scripts/lrw.sh e2e up > double.vars

# run all e2e tests
e2e-test:
	./scripts/wait_for_server_ready.sh 12 # 12 services should have log, 2 gateways has no log
	cat double.vars
	source double.vars && PIPENV_PIPFILE=backend/Pipfile pipenv run pytest \
		backend/tests/e2e_tests -k "$(T)" -W ignore::DeprecationWarning

.PHONY: test alltest e2e build-e2e double-env e2e-test

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
	cd backend && pipenv run python3 setup.py develop


backend-test: backend-install
	PIPENV_PIPFILE=backend/Pipfile pipenv run pytest \
		--ignore=backend/tests/e2e_tests backend/tests -k "$(T)" -W ignore::DeprecationWarning


.PHONY: pyre check format backend-install backend-test
