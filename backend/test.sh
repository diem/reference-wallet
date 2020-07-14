#!/bin/bash -xv

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# NOTE: each of these test modules need to be run independently due to how they
#       instantiate dramatiq and other test dependencies in conftest.py
pipenv run python3 setup.py pytest --addopts="tests/wallet_tests $@"
pipenv run python3 setup.py pytest --addopts="tests/webapp_tests $@"
pipenv run python3 setup.py pytest --addopts="tests/utils_tests $@"
pipenv run python3 setup.py pytest --addopts="tests/pubsub_tests $@"

pipenv run black --check .
#pipenv run pyre --preserve-pythonpath check
