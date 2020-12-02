# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import datetime
from typing import NewType
from uuid import UUID

from dataclasses_json import dataclass_json

from .currency import CurrencyPair

QuoteId = NewType("QuoteId", UUID)


@dataclass_json
@dataclass
class Rate:
    pair: CurrencyPair
    rate: int


@dataclass_json
@dataclass
class QuoteData:
    quote_id: QuoteId
    rate: Rate
    expires_at: datetime
    amount: int
