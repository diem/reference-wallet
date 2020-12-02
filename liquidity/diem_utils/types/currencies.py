# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing
from enum import Enum


class DiemCurrency(str, Enum):
    Coin1 = "Coin1"


class FiatCurrency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    JPY = "JPY"


Currencies = typing.Union[FiatCurrency, DiemCurrency]

DEFAULT_DIEM_CURRENCY = DiemCurrency.Coin1.value
