#!/usr/bin/env bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

if [[ -z ${LRW_KEYSTORE_B64+x} ]]; then
    echo "no keystore (base64) supplied in LRW_KEYSTORE_B64"
    exit -1
fi

if [[ -z ${GOOGLE_SERVICE_ACCOUNT_B64+x} ]]; then
    echo "no google service account key json (base64) supplied in GOOGLE_SERVICE_ACCOUNT_B64"
    exit -1
fi

if [[ -z ${STORE_PASSWORD+x} ]]; then
    echo "no keystore password supplied in STORE_PASSWORD"
    exit -1
fi

if [[ -z ${KEY_PASSWORD+x} ]]; then
    echo "no key entry (alias) password supplied in KEY_PASSWORD"
    exit -1
fi

if [[ -z ${VERSION_CODE+x} ]]; then
    echo "no version code supplied in VERSION_CODE"
    exit -1
fi

echo ${GOOGLE_SERVICE_ACCOUNT_B64} | base64 -d > /tmp/key.json
echo ${LRW_KEYSTORE_B64} | base64 -d > /tmp/lrw-release-key.keystore


fastlane beta