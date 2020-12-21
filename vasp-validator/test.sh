#!/usr/bin/env sh

#
# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
#

# If first argument is not a flag, it's a subtest selector
if [ "${1#-}" == "${1}" ]; then
  subtests=$1
  shift
fi

tests_selector=vasp_validator.tests${subtests:+.}${subtests}
pipenv run pytest -p vasp_validator.tests.plugin --pyargs ${tests_selector} "$@" ./tests
