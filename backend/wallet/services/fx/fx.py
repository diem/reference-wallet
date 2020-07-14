# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra_utils.precise_amount import Amount
from libra_utils.types.liquidity.currency import Currency, CurrencyPair, CurrencyPairs
from sdks.lp_client import LpClient
from wallet.services.fx.fx_conversions import MULTI_STEP_CONVERSION_TABLE


def get_rate(base_currency: Currency, quote_currency: Currency) -> Amount:
    try:
        return _get_rate_internal(
            base_currency=base_currency, quote_currency=quote_currency
        )
    except LookupError:
        rate = _get_rate_internal(
            base_currency=quote_currency, quote_currency=base_currency
        )
        unit = Amount().deserialize(Amount.unit)

        rate = unit / rate

        return rate


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
