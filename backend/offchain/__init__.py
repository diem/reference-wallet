# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context, uuid
from offchainapi.libra_address import LibraAddress


def get_new_offchain_reference_id(sender_address_hex: str) -> str:
    address = LibraAddress.from_hex(
        context.get().config.diem_address_hrp(), sender_address_hex, None
    )
    id = uuid.uuid1().hex
    return f"{address.as_str()}_{id}"
