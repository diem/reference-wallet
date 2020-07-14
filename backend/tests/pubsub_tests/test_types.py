# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

import libra_utils.libra
from pubsub import types


def test_bytes_parse() -> None:
    to_subaddr = os.urandom(8)

    # from and reference not present
    meta = libra_utils.libra.TransactionMetadata.from_bytes(
        b"\x01" + to_subaddr + b"\x00\x00"
    )
    assert meta.to_subaddress == to_subaddr

    # reference not present
    from_subaddr = os.urandom(8)
    meta = libra_utils.libra.TransactionMetadata.from_bytes(
        b"\x01" + to_subaddr + b"\x01" + from_subaddr + b"\x00"
    )
    assert meta.to_subaddress == to_subaddr and meta.from_subaddress == from_subaddr

    # everything present
    referenced_event = b"fakeevent"
    meta = libra_utils.libra.TransactionMetadata.from_bytes(
        b"\x01" + to_subaddr + b"\x01" + from_subaddr + b"\x01" + referenced_event
    )
    assert (
        meta.to_subaddress == to_subaddr
        and meta.from_subaddress == from_subaddr
        and meta.referenced_event == referenced_event
    )

    # malformed, but shouldn't error out. expect empty TransactionMetadata object
    meta = libra_utils.libra.TransactionMetadata.from_bytes(
        b"\x01" + to_subaddr + b"\x01" + b"\x00" + b"\x01" + b"\x00"
    )
    assert meta and not (
        meta.to_subaddress or meta.from_subaddress or meta.referenced_event
    )
