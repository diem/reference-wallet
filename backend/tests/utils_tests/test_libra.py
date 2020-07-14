# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

from pubsub.types import TransactionMetadata
from libra_utils.libra import (
    gen_raw_subaddr,
    encode_txn_metadata,
    decode_txn_metadata,
    encode_full_addr,
    decode_subaddr,
    decode_full_addr,
)


def test_encode_decode_metadata() -> None:
    meta = TransactionMetadata(gen_raw_subaddr(), gen_raw_subaddr(), os.urandom(20),)
    meta_bytes = encode_txn_metadata(meta)
    assert meta == decode_txn_metadata(meta_bytes)


def test_address_encoding() -> None:
    addr = "46db232847705e05525db0336fd9f337"
    subaddr = "5ade474482039e2a"
    full_address = encode_full_addr(vasp_addr=addr, subaddr=subaddr)

    assert full_address == "tlb1pgmdjx2z8wp0q25jakqeklk0nxaddu36ysgpeu2setn5us"


def test_address_decoding() -> None:
    full_address = "tlb1pgmdjx2z8wp0q25jakqeklk0nxaddu36ysgpeu2setn5us"
    decoded_addr, decoded_subaddr = decode_full_addr(encoded_address=full_address)
    assert decoded_addr == "46db232847705e05525db0336fd9f337"
    assert decoded_subaddr == "5ade474482039e2a"
