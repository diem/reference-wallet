# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from libra_utils.precise_amount import Amount
from libra_utils.types.liquidity.currency import CurrencyPairs


class FxTypes(Enum):
    Fx = lambda x: x
    ReverseFx = lambda x: Amount().deserialize(Amount.unit) / x


MULTI_STEP_CONVERSION_TABLE = {
    "GBP_Coin2": [
        (CurrencyPairs.GBP_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.ReverseFx),
    ],
    "Coin2_AUD": [
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.AUD_Coin1.value, FxTypes.ReverseFx),
    ],
    "Coin2_NZD": [
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.NZD_Coin1.value, FxTypes.ReverseFx),
    ],
    "Coin2_JPY": [
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_JPY.value, FxTypes.Fx),
    ],
    "Coin2_CHF": [
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_CHF.value, FxTypes.Fx),
    ],
    "Coin2_CAD": [
        (CurrencyPairs.Coin2_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_CAD.value, FxTypes.Fx),
    ],
    "LBR_AUD": [
        (CurrencyPairs.LBR_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.AUD_Coin1.value, FxTypes.ReverseFx),
    ],
    "LBR_NZD": [
        (CurrencyPairs.LBR_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.NZD_Coin1.value, FxTypes.ReverseFx),
    ],
    "LBR_JPY": [
        (CurrencyPairs.LBR_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_JPY.value, FxTypes.Fx),
    ],
    "LBR_CHF": [
        (CurrencyPairs.LBR_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_CHF.value, FxTypes.Fx),
    ],
    "LBR_CAD": [
        (CurrencyPairs.LBR_Coin1.value, FxTypes.Fx),
        (CurrencyPairs.Coin1_CAD.value, FxTypes.Fx),
    ],
}
