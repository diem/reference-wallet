# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from typing import NewType, Optional
from uuid import UUID

from dataclasses_json import dataclass_json

from .currency import CurrencyPair
from .quote import QuoteData


class Direction(str, Enum):
    Buy = "Buy"
    Sell = "Sell"


TradeId = NewType("TradeId", UUID)


@dataclass_json
@dataclass
class AddressSequence:
    address: str
    sequence: int


class TradeStatus(str, Enum):
    Pending = "Pending"
    Complete = "Complete"
    Consolidated = "Consolidated"


@dataclass_json
@dataclass
class TradeData:
    trade_id: TradeId
    direction: Direction
    pair: CurrencyPair
    amount: float
    status: TradeStatus
    quote: QuoteData
    tx_version: Optional[int] = None
