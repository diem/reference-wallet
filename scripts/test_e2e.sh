#!/bin/bash

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

#
# Runs e2e test against double-VASP docker-compose, using the `test-runner` container.
#
# Upon double-VASP instantiation, you'll have access to environment variables we need for test:
#       $ eval $(./scripts/lrw.sh double up)
#
# To run e2e test:
# cd libra-reference-wallet
# ./scripts/lrw.sh build 8080 e2e
# ./scripts/lrw.sh e2e double up > double.vars
# cat double.vars
# source double.vars && ./scripts/test_e2e.sh double
#
  # You may also visit the frontends locally via https://localhost:<GW_PORT_*>
#

single_double=$1

run_single_e2e_test() {
    if [ -z "$LRW_WEB_1" ] || [ -z "$GW_PORT_1" ] || [ -z "$VASP_ADDR_1" ] || [ -z "$GW_OFFCHAIN_SERVICE_PORT_1" ]; then

        echo "Missing environment variables, exiting..."
        exit 1

    fi

    docker exec -e GW_PORT_1 -e VASP_ADDR_1 -e LRW_WEB_1 -e GW_OFFCHAIN_SERVICE_PORT_1 \
        test-runner pytest tests/e2e_tests/single
}

run_double_e2e_test() {
    if [ -z "$LRW_WEB_1" ] || [ -z "$LRW_WEB_2" ] || \
        [ -z "$GW_PORT_1" ] || [ -z "$GW_PORT_2" ] || \
        [ -z "$VASP_ADDR_1" ] || [ -z "$VASP_ADDR_2" ] || \
        [ -z "$GW_OFFCHAIN_SERVICE_PORT_1" ] || [ -z "$GW_OFFCHAIN_SERVICE_PORT_2" ]; then

        echo "Missing environment variables, exiting..."
        exit 1

    fi

    docker exec -e GW_PORT_1 -e GW_PORT_2 \
        -e VASP_ADDR_1 -e VASP_ADDR_2 \
        -e LRW_WEB_1 -e LRW_WEB_2 \
        -e GW_OFFCHAIN_SERVICE_PORT_1 -e GW_OFFCHAIN_SERVICE_PORT_2 \
        test-runner \
        pytest tests/e2e_tests/double
}

# show environment variables primarily for debugging
export LRW_WEB_1="http://lrw_gateway_1:8000"
export LRW_WEB_2="http://lrw2_gateway_1:8000"
echo "LRW_WEB_1 = $LRW_WEB_1"
echo "GW_PORT_1 = $GW_PORT_1"
echo "VASP_ADDR_1 = $VASP_ADDR_1"
echo "GW_OFFCHAIN_SERVICE_PORT_1 = $GW_OFFCHAIN_SERVICE_PORT_1"

if [ "$single_double" = "single" ]; then
    run_single_e2e_test

elif [ "$single_double" = "double" ]; then
    echo "LRW_WEB_2 = $LRW_WEB_2"
    echo "GW_PORT_2 = $GW_PORT_2"
    echo "VASP_ADDR_2 = $VASP_ADDR_2"
    echo "GW_OFFCHAIN_SERVICE_PORT_2 = $GW_OFFCHAIN_SERVICE_PORT_2"
    run_double_e2e_test
else
    echo "Must specify single or double for e2e test suite"
    exit 1
fi
