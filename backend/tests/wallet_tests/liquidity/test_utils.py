# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair


def test_is_not_libra_to_libra():
    pair = CurrencyPairs.Coin2_USD.value

    assert CurrencyPair.is_libra_to_libra(pair) is False


def test_is_libra_to_libra():
    pair = CurrencyPairs.Coin2_Coin1.value

    assert CurrencyPair.is_libra_to_libra(pair) is True
