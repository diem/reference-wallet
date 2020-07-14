# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from libra_utils.types.liquidity.currency import CurrencyPairs, Currency
from wallet.services.fx.fx import get_rate

rates = {
    str(CurrencyPairs.Coin1_USD.value): 1000000,
    str(CurrencyPairs.Coin2_EUR.value): 1000000,
    str(CurrencyPairs.Coin2_USD.value): 1080000,
    str(CurrencyPairs.EUR_Coin1.value): 1080000,
    str(CurrencyPairs.Coin2_Coin1.value): 1080000,
    str(CurrencyPairs.Coin1_JPY.value): 107500000,
    str(CurrencyPairs.Coin1_CHF.value): 980000,
    str(CurrencyPairs.GBP_Coin1.value): 1230000,
    str(CurrencyPairs.Coin1_CAD.value): 1410000,
    str(CurrencyPairs.AUD_Coin1.value): 640000,
    str(CurrencyPairs.NZD_Coin1.value): 600000,
    str(CurrencyPairs.LBR_USD.value): 999000000,
    str(CurrencyPairs.LBR_Coin1.value): 999000000,
    str(CurrencyPairs.LBR_EUR.value): 999000000,
    str(CurrencyPairs.LBR_Coin2.value): 999000000,
    str(CurrencyPairs.LBR_GBP.value): 999000000,
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


def test_all_two_steps_conversion_rates():
    assert get_rate(Currency.GBP, Currency.Coin2).serialize() == 1138889
    assert get_rate(Currency.Coin2, Currency.GBP).serialize() == 878049

    assert get_rate(Currency.Coin2, Currency.AUD).serialize() == 1687500
    assert get_rate(Currency.Coin2, Currency.NZD).serialize() == 1800000
    assert get_rate(Currency.Coin2, Currency.JPY).serialize() == 116100000
    assert get_rate(Currency.Coin2, Currency.CHF).serialize() == 1058400
    assert get_rate(Currency.Coin2, Currency.CAD).serialize() == 1522800
    assert get_rate(Currency.LBR, Currency.AUD).serialize() == 1560937500
    assert get_rate(Currency.LBR, Currency.NZD).serialize() == 1665000333
    assert get_rate(Currency.LBR, Currency.JPY).serialize() == 107392500000
    assert get_rate(Currency.LBR, Currency.CHF).serialize() == 979020000
    assert get_rate(Currency.LBR, Currency.CAD).serialize() == 1408590000
