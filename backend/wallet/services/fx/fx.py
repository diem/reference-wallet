# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from itertools import chain
from diem_utils.precise_amount import Amount
from diem_utils.sdks.liquidity import LpClient
from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from diem_utils.types.liquidity.currency import Currency, CurrencyPair, CurrencyPairs

RATES = {}


def get_rate(base_currency: Currency, quote_currency: Currency) -> Amount:
    pair_str = str(CurrencyPair(base_currency, quote_currency))
    if pair_str not in RATES:
        update_rates()
    return RATES[pair_str]


def update_rates():
    all_currencies = [
        Currency(c)
        for c in chain(list(FiatCurrency.__members__), list(DiemCurrency.__members__))
    ]
    base_currencies = [Currency(c) for c in DiemCurrency]

    for base_currency in base_currencies:
        for quote_currency in all_currencies:
            if base_currency == quote_currency:
                continue

            try:
                _set_rate(base_currency, quote_currency)
            except LookupError:
                _set_rate(quote_currency, base_currency)


def _set_rate(base_currency: Currency, quote_currency: Currency):
    global RATES
    rate = _get_rate_internal(
        base_currency=base_currency, quote_currency=quote_currency
    )
    RATES[str(CurrencyPair(base_currency, quote_currency))] = rate
    unit = Amount().deserialize(Amount.unit)
    rate = unit / rate
    RATES[str(CurrencyPair(quote_currency, base_currency))] = rate


def _get_rate_internal(base_currency: Currency, quote_currency: Currency) -> Amount:
    currency_pair = CurrencyPair(base_currency, quote_currency)
    pair_str = f"{base_currency.value}_{quote_currency.value}"

    if pair_str in CurrencyPairs.__members__:
        quote = LpClient().get_quote(pair=currency_pair, amount=1)
        return Amount().deserialize(quote.rate.rate)

    raise LookupError(f"No conversion to currency pair {currency_pair}")
