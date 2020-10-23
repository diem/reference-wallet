# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


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


test: backend-test e2e


backend-test:
	PIPENV_PIPFILE=backend/Pipfile ./backend/test.sh


e2e: clean-docker build-e2e single double


# build e2e double test images and setup env variables
build-e2e:
	./scripts/lrw.sh build 8080 e2e


# run e2e single test
single:
	./scripts/lrw.sh e2e single up > single.vars
	# 7 services should have log, 1 gateway has no log
	./scripts/wait_for_server_ready.sh 7
	cat single.vars
	source single.vars && ./scripts/test_e2e.sh single

# run e2e double test
double:
	./scripts/lrw.sh e2e double up > double.vars
	# 14 services should have log, 2 gateways has no log
	./scripts/wait_for_server_ready.sh 14
	cat double.vars
	source double.vars && ./scripts/test_e2e.sh double


.PHONY: test backend-test e2e build-e2e single double
