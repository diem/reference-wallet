#!/usr/bin/env sh

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


# This is the list of existing hook scripts
# All the hook scripts must be inside scripts directory
hooks=pre-commit

a="/$0"; a=${a%/*}; a=${a#/}; a=${a:-.}
scripts_dir=$(cd "$a"; pwd)

get_path="git rev-parse --git-path hooks"

for hook in "${hooks}"; do
    echo Installing ${hook}
    cp ${scripts_dir}/${hook} $(${get_path})/${hook} || exit 1
done

echo Done.

