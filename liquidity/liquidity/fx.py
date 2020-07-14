# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair
from libra_utils.types.liquidity.quote import Rate

fixed_rates = {
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
    str(CurrencyPairs.LBR_USD.value): 1040000,
    str(CurrencyPairs.LBR_Coin1.value): 1040000,
    str(CurrencyPairs.LBR_EUR.value): 1030000,
    str(CurrencyPairs.LBR_Coin2.value): 1030000,
    str(CurrencyPairs.LBR_GBP.value): 1020000,
}


def get_rate(currency_pair: CurrencyPair) -> Rate:
    try:
        return Rate(currency_pair, fixed_rates[str(currency_pair)])
    except KeyError:
        raise KeyError(f"LP does not support currency pair {currency_pair}")
