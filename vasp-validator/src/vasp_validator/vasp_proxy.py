#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TxStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TxState:
    onchain_version: Optional[int] = None
    offchain_refid: Optional[str] = None
    status_description: Optional[str] = None
    status: TxStatus = TxStatus.COMPLETED


class VaspProxy(ABC):
    @abstractmethod
    def get_receiving_address(self) -> str:
        ...

    @abstractmethod
    def send_transaction(self, address: str, amount: int, currency: str) -> TxState:
        ...

    @abstractmethod
    def knows_transaction(self, version) -> bool:
        ...

    @abstractmethod
    def get_offchain_state(self, reference_id: str):
        ...
