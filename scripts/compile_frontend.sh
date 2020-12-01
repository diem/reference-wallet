#!/usr/bin/env bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

script_dir="$(dirname "$0")"
project_dir="$(dirname "$script_dir")"

docker build -t reference-wallet-frontend-build -f "${project_dir}/frontend/Dockerfile" "${project_dir}/frontend/"
