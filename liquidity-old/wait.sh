#!/usr/bin/env bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

HOST=$1
PORT=$2

if [ -z $HOST ] || [ -z $PORT ]; then
    echo "Missing HOST or PORT"
    exit 1
fi

for attempt in {1..60} ; do
    nc -z $HOST $PORT && echo "Ping successful!" && exit 0 || sleep 3
    echo "Attempt $attempt: $HOST:$PORT unreachable, sleeping..."
done
echo "ERROR: timed out"
exit 1

