#!/usr/bin/env sh

#
# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
#

echo "> Running Black"
pipenv run black .
echo

echo "> Running flake8"
pipenv run flake8 . 

