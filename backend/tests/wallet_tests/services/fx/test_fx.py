# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from diem_utils.types.liquidity.currency import CurrencyPairs, Currency
from wallet.services.fx.fx import get_rate

rates = {
    str(CurrencyPairs.Coin1_USD.value): 1000000,
    str(CurrencyPairs.EUR_Coin1.value): 1080000,
    str(CurrencyPairs.Coin1_JPY.value): 107500000,
    str(CurrencyPairs.Coin1_CHF.value): 980000,
    str(CurrencyPairs.GBP_Coin1.value): 1230000,
    str(CurrencyPairs.Coin1_CAD.value): 1410000,
    str(CurrencyPairs.AUD_Coin1.value): 640000,
    str(CurrencyPairs.NZD_Coin1.value): 600000,
}


def test_get_rate_direct_conversion_matching_currencies():
    rate = get_rate(Currency.Coin1, Currency.USD).serialize()

    assert rate == 1000000


def test_get_rate_direct_conversion_odd_currencies():
    rate = get_rate(Currency.EUR, Currency.Coin1).serialize()

    assert rate == 1080000


def test_get_rate_non_exist_conversion():
    with pytest.raises(LookupError):
        get_rate(Currency.CHF, Currency.NZD).serialize()
