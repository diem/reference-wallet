#!/bin/bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

export FLASK_ENV=${COMPOSE_ENV:-development}
export FLASK_APP="webapp:init()"

pipenv run flask run --host 0.0.0.0 --port ${WALLET_PORT:-5000} --no-reload
