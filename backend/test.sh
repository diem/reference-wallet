#!/bin/bash -xv

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -euo pipefail

# NOTE: each of these test modules need to be run independently due to how they
#       instantiate dramatiq and other test dependencies in conftest.py
pipenv run python3 $DIR/setup.py pytest --addopts="$DIR/tests/wallet_tests $@"
pipenv run python3 $DIR/setup.py pytest --addopts="$DIR/tests/webapp_tests $@"
pipenv run python3 $DIR/setup.py pytest --addopts="$DIR/tests/pubsub_tests $@"
pipenv run python3 $DIR/setup.py pytest --addopts="$DIR/tests/offchain_tests $@"
pipenv run python3 $DIR/setup.py pytest --addopts="$DIR/tests/context_tests $@"

pipenv run black --check $DIR
#pipenv run pyre --preserve-pythonpath check
