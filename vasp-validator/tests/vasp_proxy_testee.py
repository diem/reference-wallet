#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
from vasp_validator import ValidatorClient
from vasp_validator.models_fppa import FundPullPreApprovalScope
from vasp_validator.vasp_proxy import VaspProxy, TxState


class VaspProxyTestee(VaspProxy):
    """
    This class emulates VASP under test.
    Since, for the testing purposes, both the validator and the testee are
    represented by an instance of the Reference Wallet, this class is just
    a naive wrapper for ValidationClient. We could have used ValidationClient
    directly but then it would have been too confusing.
    """

    def __init__(self, url):
        self.vasp = ValidatorClient.create(url, "vasp-proxy-testee")

    def get_receiving_address(self) -> str:
        return self.vasp.get_receiving_address()

    def send_transaction(self, address: str, amount: int, currency: str) -> TxState:
        return self.vasp.send_transaction(address, amount, currency)

    def knows_transaction_by_version(self, version) -> bool:
        return self.vasp.knows_transaction_by_version(version)

    def knows_transaction_by_reference_id(self, reference_id) -> bool:
        return self.vasp.knows_transaction_by_reference_id(reference_id)

    def get_offchain_state(self, reference_id: str):
        return self.vasp.get_offchain_state(reference_id)

    def request_funds_pull_preapproval_from_another(
        self,
        payer_addr_bech32: str,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        return self.vasp.request_funds_pull_preapproval_from_another(
            payer_addr_bech32=payer_addr_bech32,
            scope=scope,
            description=description,
        )

    def create_fppa_request_for_unknown_payer(
        self,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        return self.vasp.create_and_approve_funds_pull_request(scope, description)

    def get_all_funds_pull_preapprovals(self):
        return self.vasp.get_all_funds_pull_preapprovals()

    def approve_funds_pull_request(self, funds_pre_approval_id: str):
        return self.vasp.approve_funds_pull_request(funds_pre_approval_id)

    def reject_funds_pull_request(self, funds_pre_approval_id: str):
        return self.vasp.reject_funds_pull_request(funds_pre_approval_id)

    def close_funds_pull_preapproval(self, funds_pre_approval_id: str):
        return self.vasp.close_funds_pull_preapproval(funds_pre_approval_id)

    def create_and_approve_funds_pull_request(
        self,
        biller_address: str,
        funds_pull_pre_approval_id: str,
        scope: FundPullPreApprovalScope,
        description: str,
    ):
        return self.vasp.create_and_approve_funds_pull_request(
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            scope=scope,
            description=description,
        )

    def create_payment_command_as_sender(
        self,
        reference_id,
        vasp_address,
        merchant_name,
        action,
        currency,
        amount,
        expiration,
    ):
        self.vasp.create_payment_command_as_sender(
            reference_id=reference_id,
            vasp_address=vasp_address,
            merchant_name=merchant_name,
            action=action,
            currency=currency,
            amount=amount,
            expiration=expiration,
        )

    def approve_payment_command(self, reference_id):
        self.vasp.approve_payment_command(reference_id)

    def reject_payment_command(self, reference_id):
        self.vasp.reject_payment_command(reference_id)

    def get_payment_details(self, reference_id, vasp_address):
        return self.vasp.get_payment_details(reference_id, vasp_address)

    def prepare_payment_as_receiver(self, action):
        return self.vasp.prepare_payment_as_receiver(action)

    def approve_payment(self, reference_id, init_offchain):
        return self.vasp.approve_payment(reference_id, init_offchain)
