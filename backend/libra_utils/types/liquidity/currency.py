# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum

from dataclasses_json import dataclass_json


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    JPY = "JPY"

    LBR = "LBR"
    Coin1 = "Coin1"
    Coin2 = "Coin2"


FIAT_CURRENCIES = [
    Currency.USD,
    Currency.EUR,
    Currency.GBP,
    Currency.CHF,
    Currency.CAD,
    Currency.AUD,
    Currency.NZD,
    Currency.JPY,
]


def is_fiat(currency: Currency) -> bool:
    return currency in FIAT_CURRENCIES


def is_libra(currency: Currency) -> bool:
    return currency not in FIAT_CURRENCIES


@dataclass_json
@dataclass
class CurrencyPair:
    base: Currency  # BUY / SELL currency
    quote: Currency  # The Currency you want to Pay with / Get in exchange to the base currency

    def __repr__(self):
        return f"{self.base}_{self.quote}"

    def __str__(self):
        return f"{self.base}_{self.quote}"

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def is_libra_to_libra(pair: "CurrencyPair"):
        return is_libra(pair.base) and is_libra(pair.quote)


class CurrencyPairs(Enum):
    Coin1_USD = CurrencyPair(base=Currency.Coin1, quote=Currency.USD)
    Coin2_EUR = CurrencyPair(base=Currency.Coin2, quote=Currency.EUR)

    Coin2_USD = CurrencyPair(base=Currency.Coin2, quote=Currency.USD)
    EUR_Coin1 = CurrencyPair(base=Currency.EUR, quote=Currency.Coin1)
    Coin2_Coin1 = CurrencyPair(base=Currency.Coin2, quote=Currency.Coin1)

    Coin1_JPY = CurrencyPair(base=Currency.Coin1, quote=Currency.JPY)
    Coin1_CHF = CurrencyPair(base=Currency.Coin1, quote=Currency.CHF)
    Coin1_CAD = CurrencyPair(base=Currency.Coin1, quote=Currency.CAD)

    GBP_Coin1 = CurrencyPair(base=Currency.GBP, quote=Currency.Coin1)
    AUD_Coin1 = CurrencyPair(base=Currency.AUD, quote=Currency.Coin1)
    NZD_Coin1 = CurrencyPair(base=Currency.NZD, quote=Currency.Coin1)

    LBR_USD = CurrencyPair(base=Currency.LBR, quote=Currency.USD)
    LBR_Coin1 = CurrencyPair(base=Currency.LBR, quote=Currency.Coin1)
    LBR_EUR = CurrencyPair(base=Currency.LBR, quote=Currency.EUR)
    LBR_Coin2 = CurrencyPair(base=Currency.LBR, quote=Currency.Coin2)
    LBR_GBP = CurrencyPair(base=Currency.LBR, quote=Currency.GBP)

    @staticmethod
    def from_pair(pair: CurrencyPair):
        return CurrencyPairs[str(pair)]
