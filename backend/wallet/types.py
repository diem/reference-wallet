# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Dict, NewType
from uuid import UUID

from diem_utils.types.currencies import DiemCurrency, FiatCurrency

OrderId = NewType("OrderId", UUID)


class TransactionDirection(str, Enum):
    RECEIVED = "received"
    SENT = "sent"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    READY_FOR_ON_CHAIN = "ready_for_on_chain"
    OFF_CHAIN_STARTED = "off_chain_started"


class TransactionType(str, Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    OFFCHAIN = "offchain"


class TransactionSortOption(str, Enum):
    DATE_ASC = "date_asc"
    DATE_DESC = "date_desc"
    DIEM_AMOUNT_DESC = "diem_amount_desc"
    DIEM_AMOUNT_ASC = "diem_amount_asc"
    FIAT_AMOUNT_DESC = "fiat_amount_desc"
    FIAT_AMOUNT_ASC = "fiat_amount_asc"


class DocumentType(str, Enum):
    DRIVERS_LICENSE = "drivers_license"


class RegistrationStatus(str, Enum):
    Registered = "Registered"
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


@dataclass
class UserInfo:
    id: int
    username: Optional[str]
    is_admin: bool
    is_blocked: bool
    registration_status: Optional[RegistrationStatus]
    selected_fiat_currency: FiatCurrency
    selected_language: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    zip: Optional[str] = None

    @staticmethod
    def from_obj(user):
        return UserInfo(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            registration_status=user.registration_status,
            selected_fiat_currency=user.selected_fiat_currency,
            selected_language=user.selected_language,
            first_name=user.first_name,
            last_name=user.last_name,
            dob=user.dob,
            phone=user.phone,
            country=user.country,
            state=user.state,
            city=user.city,
            address_1=user.address_1,
            address_2=user.address_2,
            zip=user.zip,
        )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "is_blocked": self.is_blocked,
            "registration_status": self.registration_status,
            "selected_fiat_currency": self.selected_fiat_currency,
            "selected_language": self.selected_language,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "phone": self.phone,
            "country": self.country,
            "state": self.state,
            "address_1": self.address_1,
            "address_2": self.address_2,
            "zip": self.zip,
        }


class OrderStatus(str, Enum):
    PendingExecution = "PendingExecution"  # Order is pending execution
    Charged = "Charged"  # Payment method charged successfully
    Executed = "Executed"  # Order has executed.
    Expired = "Expired"  # Order has expired.
    FailedExecute = "FailedExecute"  # Could not execute order.
    FailedCharge = "FailedCharge"  # Could not charge user Payment method.
    FailedCredit = "FailedCredit"  # Could not credit user Payment method.


class CoverStatus(str, Enum):
    PendingCover = "PendingCover"
    PendingCoverWithQuote = "PendingCoverWithQuote"
    PendingCoverValidation = "PendingCoverValidation"
    Covered = "Covered"
    FailedCoverLPTradeError = "FailedTradeLPError"
    FailedCoverTransactionError = "FailedCoverTransactionError"


class Direction(str, Enum):
    Buy = "Buy"
    Sell = "Sell"


class LoginError(str, Enum):
    SUCCESS = "success"
    USER_NOT_FOUND = "user_not_found"
    WRONG_PASSWORD = "wrong_password"
    UNAUTHORIZED = "unauthorized"
    ADMIN_DISABLED = "admin_disabled"


class UsernameExistsError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConvertResult(str, Enum):
    Success = ("Success",)
    InsufficientBalance = "InsufficientBalance"
    InsufficientInventoryBalance = "InsufficientInventoryBalance"
    TransferFailure = "TransferFailure"


class BalanceError(Exception):
    """ Indicates a insufficient funds """

    pass


class PaymentMethodAction(Enum):
    Charge = "Charge"
    Refund = "Refund"


class OrderType(str, Enum):
    Trade = "Trade"
    DirectConvert = "DirectConvert"  # Diem sub currency to Diem sub currency.


class Balance:
    def __init__(self):
        self.total: Dict[DiemCurrency, int] = {
            DiemCurrency.Coin1: 0,
        }
        self.frozen: Dict[DiemCurrency, int] = {
            DiemCurrency.Coin1: 0,
        }


class UserNotFoundError(Exception):
    pass
