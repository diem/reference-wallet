# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import logging

logger = logging.getLogger(name="wallet-service-transaction")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

_RUN_BACKGROUND_TASKS = bool(os.getenv("RUN_BACKGROUND_TASKS", True))


def run_bg_tasks() -> bool:
    return _RUN_BACKGROUND_TASKS


INVENTORY_ACCOUNT_NAME = "Inventory"
