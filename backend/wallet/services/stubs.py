import typing
from dataclasses import dataclass, field as datafield
from enum import Enum

from diem.offchain import (
    CommandType,
)
from diem.offchain.types.data_types import UUID_REGEX, PaymentCommandObject
from diem_utils.types.currencies import DiemCurrency


@dataclass(frozen=True)
class CurrencyObject(object):
    amount: int
    currency: str = datafield(default=DiemCurrency.XUS)


class ScopeUnitType(str, Enum):
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass(frozen=True)
class ScopedCumulativeAmountObject:
    unit: str = datafield(
        metadata={"valid-values": typing.Union[ScopeUnitType]},
    )
    value: int
    max_amount: CurrencyObject


class ScopeType(str, Enum):
    CONSENT = "consent"
    SAVE_SUB_ACCOUNT = "save_sub_account"


@dataclass(frozen=True)
class ScopeObject:
    type: str = datafield(
        metadata={"valid-values": typing.Union[ScopeType]},
    )
    expiration_time: int
    max_cumulative_amount: typing.Optional[ScopedCumulativeAmountObject] = datafield(
        default=None
    )
    max_transaction_amount: typing.Optional[CurrencyObject] = datafield(default=None)


@dataclass(frozen=True)
class FundPullPreApprovalObject:
    address: str
    biller_address: str
    funds_pre_approval_id: str = datafield(metadata={"valid-values": UUID_REGEX})
    scope: ScopeObject
    description: str
    status: str = datafield(
        default="pending",
        metadata={"valid-values": ["pending", "valid", "rejected", "closed"]},
    )


@dataclass(frozen=True)
class FundPullPreApprovalCommandObject:
    _ObjectType: str = datafield(
        metadata={"valid-values": [CommandType.FundPullPreApprovalCommand]}
    )
    fund_pull_pre_approval: FundPullPreApprovalObject


@dataclass(frozen=True)
class CommandRequestObject:
    # A unique identifier for the Command.
    cid: str = datafield(metadata={"valid-values": UUID_REGEX})
    # A string representing the type of Command contained in the request.
    command_type: str = datafield(
        metadata={
            "valid-values": [
                CommandType.PaymentCommand,
                CommandType.FundPullPreApprovalCommand,
            ]
        }
    )
    command: typing.Union[FundPullPreApprovalCommandObject, PaymentCommandObject]
    _ObjectType: str = datafield(
        default="CommandRequestObject",
        metadata={"valid-values": ["CommandRequestObject"]},
    )
