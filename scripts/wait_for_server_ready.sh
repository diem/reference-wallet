#!/usr/bin/env bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

service_num=$1

for attempt in {1..60} ; do
    logs=$(docker ps -a | awk '{ print $1 }' | awk 'NR>1' | xargs -L1 -I {} sh -c "docker logs {} 2>&1 | tail -1")
    lines=$(echo "$logs"| wc -l)
    echo "tail logs lines: $lines, expect: $service_num"
    unreachable=$(echo "$logs"| grep unreachable || true)
    echo "unreachable: $unreachable"
    if [ $lines -ge $service_num ]; then
        if [ -z "$unreachable" ]; then
	    echo "All services reachable"
	    exit 0
        fi
    fi

    echo "Attempt $attempt, some services still unreachable"
    sleep 3
done
echo "Services unhealthy"
exit 1
