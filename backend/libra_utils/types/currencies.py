# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing
from enum import Enum


class LibraCurrency(str, Enum):
    LBR = "LBR"
    Coin1 = "Coin1"
    Coin2 = "Coin2"


class FiatCurrency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    JPY = "JPY"


Currencies = typing.Union[FiatCurrency, LibraCurrency]
