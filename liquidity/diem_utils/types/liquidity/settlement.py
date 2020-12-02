# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import NewType

from dataclasses_json import dataclass_json

from .currency import Currency

DebtId = NewType("DebtId", uuid.UUID)


@dataclass_json
@dataclass
class DebtData:
    debt_id: DebtId
    currency: Currency
    amount: int  # Positive value - Wallet owes LP, negative value - LP owes Wallet
