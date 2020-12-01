#!/bin/bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

PROCS=${PROCS:-2}
THREADS=${THREADS:-2}

if [ -z "${PROCS##*[!0-9]*}" ] || [ -z "${THREADS##*[!0-9]*}" ]; then
    echo "PROCS and THREADS env vars should be integers"
    exit 1
fi

dramatiq wallet -p $PROCS -t $THREADS --verbose --watch . "$@"
