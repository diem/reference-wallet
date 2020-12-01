# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing
from offchainapi.core import Vasp


_offchain_client: typing.Optional[Vasp] = None


def set(vasp: typing.Optional[Vasp]) -> None:
    global _offchain_client
    _offchain_client = vasp


def get() -> Vasp:
    global _offchain_client
    if _offchain_client is None:
        raise ValueError("global offchain client is not initialized")
    return typing.cast(Vasp, _offchain_client)
