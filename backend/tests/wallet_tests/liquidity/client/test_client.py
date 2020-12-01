# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

# import pytest
#
# from diem_utils.types.liquidity.currency import CurrencyPair, Currency
# from liquidity.fx import fixed_rates
# from wallet.lp_client import LpClient
#
#
# def test_get_quote_for_supported_currency_pair(liquidity_provider_session):
#     pair = CurrencyPair(Currency.Coin1, Currency.USD)
#     quote = LpClient().get_quote(pair, 1)
#
#     assert quote.rate.rate == fixed_rates[str(pair)]
#     assert quote.rate.pair == pair
#
#
# def test_get_quote_unsupported_currency_pair(liquidity_provider_session):
#     with pytest.raises(LookupError):
#         pair = CurrencyPair(Currency.CHF, Currency.USD)
#         LpClient().get_quote(pair, 1)
