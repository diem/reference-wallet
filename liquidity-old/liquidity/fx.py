# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair
from diem_utils.types.liquidity.quote import Rate

fixed_rates = {
    str(CurrencyPairs.Coin1_EUR.value): 926000,
    str(CurrencyPairs.Coin1_USD.value): 1000000,
    str(CurrencyPairs.EUR_Coin1.value): 1080000,
    str(CurrencyPairs.Coin1_JPY.value): 107500000,
    str(CurrencyPairs.Coin1_CHF.value): 980000,
    str(CurrencyPairs.GBP_Coin1.value): 1230000,
    str(CurrencyPairs.Coin1_CAD.value): 1410000,
    str(CurrencyPairs.AUD_Coin1.value): 640000,
    str(CurrencyPairs.NZD_Coin1.value): 600000,
}


def get_rate(currency_pair: CurrencyPair) -> Rate:
    try:
        return Rate(currency_pair, fixed_rates[str(currency_pair)])
    except KeyError:
        raise KeyError(f"LP does not support currency pair {currency_pair}")
