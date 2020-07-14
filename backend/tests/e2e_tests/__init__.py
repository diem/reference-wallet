# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Callable

LRW_WEB_1 = os.getenv("LRW_WEB_1")
LRW_WEB_2 = os.getenv("LRW_WEB_2")
GW_PORT_1 = os.getenv("GW_PORT_1")
GW_PORT_2 = os.getenv("GW_PORT_2")
VASP_ADDR_1 = os.getenv("VASP_ADDR_1")
VASP_ADDR_2 = os.getenv("VASP_ADDR_2")

print(LRW_WEB_1)
print(LRW_WEB_2)
print(GW_PORT_1)
print(GW_PORT_2)
print(VASP_ADDR_1)
print(VASP_ADDR_2)


class Doubler:
    def __init__(self, func: Callable[[str], None]) -> None:
        self.func: Callable[[str], None] = func

    def exec(self) -> None:
        self.func(LRW_WEB_1)
        self.func(LRW_WEB_2)
