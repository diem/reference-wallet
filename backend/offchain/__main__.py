# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from offchain import init_vasp, VASP, loop, thread

DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")
init_vasp(VASP, loop, thread)
print(f"VASP {VASP} started", flush=True)
