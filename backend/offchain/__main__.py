# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from offchain import init_vasp, vasp_obj

DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")
VASP, loop, thread = init_vasp(vasp_obj)
print(f"VASP {VASP} started", flush=True)
