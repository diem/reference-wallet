#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from dataclasses_json import dataclass_json, config

exclude_if_none = field(default=None, metadata=config(exclude=lambda x: x is None))


class TimeUnit(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


@dataclass_json
@dataclass
class CurrencyObject:
    amount: int
    currency: str


@dataclass_json
@dataclass
class ScopedCumulativeAmount:
    unit: TimeUnit
    value: int
    max_amount: CurrencyObject


class FundPullPreApprovalType(str, Enum):
    save_sub_account = "save_sub_account"
    consent = "consent"


@dataclass_json
@dataclass
class FundPullPreApprovalScope:
    type: FundPullPreApprovalType
    expiration_timestamp: int
    max_cumulative_amount: Optional[ScopedCumulativeAmount] = exclude_if_none
    max_transaction_amount: Optional[CurrencyObject] = exclude_if_none


@dataclass_json
@dataclass
class FundsPullPreApprovalRequest:
    scope: FundPullPreApprovalScope
    payer_address: Optional[str] = None
    description: Optional[str] = None


class FundPullPreApprovalStatus(str, Enum):
    # Pending user/VASP approval
    pending = "pending"
    # Approved by the user/VASP and ready for use
    valid = "valid"
    # User/VASP did not approve the pre-approval request
    rejected = "rejected"
    # Approval has been closed by the user/VASP and can no longer be used
    closed = "closed"


@dataclass_json
@dataclass
class FundsPullPreApproval:
    funds_pull_pre_approval_id: str
    address: str
    biller_address: str
    scope: FundPullPreApprovalScope
    status: FundPullPreApprovalStatus
    description: Optional[str]
