# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from itertools import chain
from libra_utils.precise_amount import Amount
from libra_utils.sdks.liquidity import LpClient
from libra_utils.types.currencies import LibraCurrency, FiatCurrency
from libra_utils.types.liquidity.currency import Currency, CurrencyPair, CurrencyPairs

from wallet.services.fx.fx_conversions import MULTI_STEP_CONVERSION_TABLE

RATES = {}


def get_rate(base_currency: Currency, quote_currency: Currency) -> Amount:
    pair_str = str(CurrencyPair(base_currency, quote_currency))
    if pair_str not in RATES:
        update_rates()

    return RATES[pair_str]


def update_rates():
    all_currencies = [
        Currency(c)
        for c in chain(list(FiatCurrency.__members__), list(LibraCurrency.__members__))
    ]
    base_currencies = [Currency(c) for c in LibraCurrency]

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

    if pair_str in MULTI_STEP_CONVERSION_TABLE:
        rate = Amount().deserialize(Amount.unit)

        steps = MULTI_STEP_CONVERSION_TABLE[pair_str]

        for step_currency_pair, fx_type in steps:
            step_quote = LpClient().get_quote(pair=step_currency_pair, amount=1)

            step_rate = fx_type(Amount().deserialize(step_quote.rate.rate))

            rate = rate * step_rate

        return rate

    raise LookupError(f"No conversion to currency pair {currency_pair}")
