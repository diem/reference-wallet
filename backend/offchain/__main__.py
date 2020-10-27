# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context

from offchain import offchain_service


offchain_service.bootstrap(context.from_env())
