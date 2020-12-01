# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair


def test_is_not_diem_to_diem():
    pair = CurrencyPairs.Coin1_USD.value

    assert CurrencyPair.is_diem_to_diem(pair) is False
