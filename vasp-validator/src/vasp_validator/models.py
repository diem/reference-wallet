#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, List

from dataclasses_json import dataclass_json


class RegistrationStatus(str, Enum):
    Registered = "Registered"
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"
    READY_FOR_ON_CHAIN = "ready_for_on_chain"
    OFF_CHAIN_STARTED = "off_chain_started"


@dataclass_json
@dataclass
class User:
    id: int
    username: Optional[str]
    is_admin: bool
    is_blocked: bool
    registration_status: Optional[RegistrationStatus]
    selected_fiat_currency: str
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


@dataclass_json
@dataclass
class Address:
    address: str


@dataclass_json
@dataclass
class Vasp:
    vasp_name: str
    user_id: str
    full_addr: str


@dataclass_json
@dataclass
class BlockchainTransaction:
    amount: int
    source: str
    destination: str
    expirationTime: str
    sequenceNumber: Optional[int]
    status: str
    version: Optional[int]


@dataclass_json
@dataclass
class Transaction:
    id: int
    amount: int
    currency: str
    direction: str
    status: TransactionStatus
    timestamp: str
    source: Vasp
    destination: Vasp
    is_internal: bool
    blockchain_tx: BlockchainTransaction


@dataclass_json
@dataclass
class Transactions:
    transaction_list: List[Transaction]


@dataclass_json
@dataclass
class RequestForQuote:
    action: str
    amount: int
    currency_pair: str


@dataclass_json
@dataclass
class Quote:
    quote_id: str
    rfq: RequestForQuote
    price: int
    expiration_time: str


@dataclass_json
@dataclass
class CreateTransaction:
    currency: str
    amount: int
    receiver_address: str


@dataclass_json
@dataclass
class Balance:
    currency: str
    balance: int


@dataclass_json
@dataclass
class AccountInfo:
    balances: List[Balance]


@dataclass_json
@dataclass
class OffChainSequenceInfo:
    pass
