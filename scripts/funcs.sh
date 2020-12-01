#!/usr/bin/env bash

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
PINK='\033[1;35m'
YELLOW='\033[0;33m'

##
# More consistent echo.
#
ec() {
  IFS=' ' printf "%b\n" "$*"
}

##
# Outputs new line.
# No parameters.
#
br() {
  ec ''
}

success() {
  ec "${GREEN}$1${NC}"
}

info() {
  ec "${PINK}$1${NC}"
}

warn() {
  ec "${YELLOW}$1${NC}"
}

error() {
  >&2 ec "${RED}ERROR: $1${NC}"
}

fail() {
  error "$@"
  exit 1
}
