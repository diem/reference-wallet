# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

_RUN_BACKGROUND_TASKS = bool(os.getenv("RUN_BACKGROUND_TASKS", True))


def run_bg_tasks() -> bool:
    return _RUN_BACKGROUND_TASKS


INVENTORY_ACCOUNT_NAME = "Inventory"
