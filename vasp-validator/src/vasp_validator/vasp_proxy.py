#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .models_fppa import FundPullPreApprovalScope


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

    @abstractmethod
    def request_funds_pull_preapproval_from_another(
        self,
        payer_addr_bech32: str,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        """
        Send a request to a user, identified by their address, to pre-approve future
        fund pulls, to be performed by this VASP.

        :param payer_addr_bech32: Bech32 encoded address of the paying user.
        :param scope: Definition of the scope of this request.
        :param description: Optional, human readable description of the request.

        :return: ID of the new funds pull pre-approval request.
        """

    @abstractmethod
    def get_all_funds_pull_preapprovals(self):
        ...

    @abstractmethod
    def approve_funds_pull_request(self, funds_pre_approval_id: str):
        ...

    @abstractmethod
    def reject_funds_pull_request(self, funds_pre_approval_id: str):
        ...

    @abstractmethod
    def close_funds_pull_preapproval(self, funds_pre_approval_id: str):
        ...
