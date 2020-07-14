#!/bin/bash

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

#export INIT_DRAMATIQ=1

dramatiq wallet -p 2 -t 2 --verbose --watch . "$@"
