# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from diem_utils.types.liquidity.currency import CurrencyPairs, Currency
from wallet.services.fx.fx import get_rate

rates = {
    str(CurrencyPairs.XUS_USD.value): 1000000,
    str(CurrencyPairs.EUR_XUS.value): 1080000,
    str(CurrencyPairs.XUS_JPY.value): 107500000,
    str(CurrencyPairs.XUS_CHF.value): 980000,
    str(CurrencyPairs.GBP_XUS.value): 1230000,
    str(CurrencyPairs.XUS_CAD.value): 1410000,
    str(CurrencyPairs.AUD_XUS.value): 640000,
    str(CurrencyPairs.NZD_XUS.value): 600000,
}


def test_get_rate_direct_conversion_matching_currencies():
    rate = get_rate(Currency.XUS, Currency.USD).serialize()

    assert rate == 1000000


def test_get_rate_direct_conversion_odd_currencies():
    rate = get_rate(Currency.EUR, Currency.XUS).serialize()

    assert rate == 1080000


def test_get_rate_non_exist_conversion():
    with pytest.raises(LookupError):
        get_rate(Currency.CHF, Currency.NZD).serialize()
