# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair


def test_is_not_libra_to_libra():
    pair = CurrencyPairs.Coin1_USD.value

    assert CurrencyPair.is_libra_to_libra(pair) is False
