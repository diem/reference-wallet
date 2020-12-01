# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env bash

if [[ -z ${APPLE_ID+x} ]]; then
    echo "no apple id supplied in APPLE_ID"
    exit -1
fi

if [[ -z ${APPLE_APP_IDENTIFIER+x} ]]; then
    echo "no apple application identifier (app id) supplied in APPLE_APP_IDENTIFIER"
    exit -1
fi

if [[ -z ${APPLE_TEAM_ID+x} ]]; then
    echo "no apple team id supplied in APPLE_TEAM_ID"
    exit -1
fi

if [[ -z ${FASTLANE_MATCH_REPO+x} ]]; then
    echo "no fastlane match repo (git url with access token) supplied in FASTLANE_MATCH_REPO"
    exit -1
fi

if [[ -z ${FASTLANE_KEYCHAIN_PWD+x} ]]; then
    echo "no fastlane keychain password supplied in FASTLANE_KEYCHAIN_PWD"
    exit -1
fi

if [[ -z ${MATCH_PASSWORD+x} ]]; then
    echo "no fastlane match storage passphrase supplied in MATCH_PASSWORD"
    exit -1
fi

if [[ -z ${PROVISIONING_PROFILE+x} ]]; then
    echo "no xcode provisioning profile specifier supplied in PROVISIONING_PROFILE"
    exit -1
fi

#cd ..
#npx yarn build:ios
#
#cd ios
bundle exec fastlane beta --verbose
