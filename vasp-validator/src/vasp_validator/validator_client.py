#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
import random
import string
import time
from typing import List

from .models import OffChainSequenceInfo, TransactionStatus, RegistrationStatus
from .models_fppa import FundPullPreApprovalScope, FundsPullPreApproval
from .models_fppa import (
    FundPullPreApprovalStatus,
)
from .reference_wallet_proxy import ReferenceWalletProxy
from .vasp_proxy import VaspProxy, TxStatus, TxState

RETRIES_COUNT = os.getenv("RETRIES_COUNT", 20)
SECONDS_BETWEEN_RETRIES = os.getenv("SECONDS_BETWEEN_RETRIES", 1)


class ValidatorClient(VaspProxy):
    def __init__(self, wallet: ReferenceWalletProxy, instance_name: str):
        self.wallet = wallet
        self.instance_name = instance_name
        self.log = logging.getLogger(instance_name)

    @classmethod
    def create(cls, wallet_url, logger_name: str) -> "ValidatorClient":
        wallet = ReferenceWalletProxy(wallet_url)
        validator = cls(wallet, logger_name)

        username = f"gurki_and_bond@{get_random_string(8)}"
        password = get_random_string(12)

        validator._create_approved_user(
            username=username,
            first_name=get_random_string(8),
            last_name=get_random_string(8),
            password=password,
        )
        validator.log.debug(f"Created user {username} (PSW: {password})")

        amount = 5_000_000_000
        validator.add_funds(amount)
        validator.log.debug(f"Added {amount} coins to the account")

        return validator

    def get_receiving_address(self) -> str:
        return self.wallet.get_receiving_address()

    def send_transaction(self, address, amount, currency) -> TxState:
        # TBD: LRW should return the offchain refid, if applicable
        tx_id = self.wallet.send_transaction(address, amount, currency)

        for i in range(RETRIES_COUNT):
            funds_transfer = self.wallet.get_transaction(tx_id.id)
            tx = funds_transfer.transaction
            if tx and (
                tx.status == TransactionStatus.CANCELED
                or tx.status == TransactionStatus.COMPLETED
            ):
                break
            time.sleep(SECONDS_BETWEEN_RETRIES)
        else:
            return TxState(
                status=TxStatus.PENDING,
                status_description="Timeout waiting for pending transaction",
            )

        if tx.status != TransactionStatus.COMPLETED:
            return TxState(
                status=TxStatus.FAILED,
                status_description=f"Send transaction was not successful ({tx})",
            )

        self.log.info(
            f"Successfully sent {amount:,} {currency} to {address}  "
            f"🟢 https://diemexplorer.com/testnet/version/{tx.blockchain_tx.version}"
        )
        return TxState(
            onchain_version=tx.blockchain_tx.version,
            # offchain_refid=tx.offchain_refid,
        )

    def knows_transaction_by_version(self, version):
        """
        Checks whether the transaction with the specified version is recognized by
        the validator as received by the current user.

        Note: Consider checking other transaction properties too;
        e.g., amount, currency etc.
        """
        for i in range(RETRIES_COUNT):
            txs = self.wallet.get_transaction_list()
            if txs and version in [
                tx.blockchain_tx.version for tx in txs if tx.blockchain_tx
            ]:
                return True
            time.sleep(SECONDS_BETWEEN_RETRIES)

        return False

    def knows_transaction_by_reference_id(self, reference_id) -> bool:
        """
        Checks whether the transaction with the specified version is recognized by
        the validator as received by the current user.

        Note: Consider checking other transaction properties too;
        e.g., amount, currency etc.
        """
        for i in range(RETRIES_COUNT):
            txs = self.wallet.get_transaction_list()
            if txs and reference_id in [tx.reference_id for tx in txs]:
                return True
            time.sleep(SECONDS_BETWEEN_RETRIES)

        return False

    def get_offchain_state(self, reference_id) -> OffChainSequenceInfo:
        return self.wallet.get_offchain_state(reference_id)

    def kyc_abort(self):
        """
        Configure the validator that all the following off-chain travel rule
        sequences should fail the KYC check.
        """

    def kyc_manual_review(self):
        """
        Configure the validator that all the following off-chain travel rule
        sequences should stop pending KYC manual review.
        """

    def add_funds(self, amount: int):
        quote_id = self.wallet.create_deposit_quote(amount, "XUS_USD").quote_id
        self.wallet.execute_quote(quote_id)

        if not self.wait_for_balance(amount, "XUS"):
            raise VaspValidatorError(
                f"Failed to validate funds in {self.instance_name}. "
                "It might be a network problem or the blockchain is inaccessible"
            )

    def wait_for_balance(self, amount, currency):
        for i in range(RETRIES_COUNT):
            if self.wallet.get_balance(currency) >= amount:
                return True
            time.sleep(SECONDS_BETWEEN_RETRIES)

        return False

    def request_funds_pull_preapproval_from_another(
        self,
        payer_addr_bech32: str,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        return self.wallet.funds_pull_preapproval.request_preapproval_from_another(
            payer_addr_bech32=payer_addr_bech32,
            scope=scope,
            description=description,
        )

    def create_fppa_request_for_unknown_payer(
        self,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ):
        return self.wallet.funds_pull_preapproval.create_fppa_request_for_unknown_payer(
            scope=scope,
            description=description,
        )

    def get_all_funds_pull_preapprovals(self) -> List[FundsPullPreApproval]:
        for i in range(RETRIES_COUNT):
            preapprovals = self.wallet.funds_pull_preapproval.get_all_preapprovals()
            if preapprovals:
                return preapprovals

            time.sleep(SECONDS_BETWEEN_RETRIES)

        return self.wallet.funds_pull_preapproval.get_all_preapprovals()

    def approve_funds_pull_request(self, funds_pre_approval_id: str):
        self.wallet.funds_pull_preapproval.update_preapproval_status(
            funds_pre_approval_id, FundPullPreApprovalStatus.valid
        )

    def reject_funds_pull_request(self, funds_pre_approval_id: str):
        self.wallet.funds_pull_preapproval.update_preapproval_status(
            funds_pre_approval_id, FundPullPreApprovalStatus.rejected
        )

    def close_funds_pull_preapproval(self, funds_pre_approval_id: str):
        self.wallet.funds_pull_preapproval.update_preapproval_status(
            funds_pre_approval_id, FundPullPreApprovalStatus.closed
        )

    def create_and_approve_funds_pull_request(
        self,
        biller_address: str,
        funds_pull_pre_approval_id: str,
        scope: FundPullPreApprovalScope,
        description: str,
    ):
        self.wallet.funds_pull_preapproval.create_and_approve(
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            scope=scope,
            description=description,
        )

    def _create_approved_user(self, username, first_name, last_name, password):
        self.wallet.create_new_user(username, password)
        user = self.wallet.get_user()

        user.first_name = first_name
        user.last_name = last_name
        user.address_1 = "221B Baker Street"
        user.address_2 = ""
        user.city = "London"
        user.country = "GB"
        user.dob = "1861-06-01"
        user.phone = "44 2079460869"
        user.selected_fiat_currency = "USD"
        user.selected_language = "en"
        user.state = ""
        user.zip = "NW1 6XE"

        user = self.wallet.update_user(user)

        for i in range(RETRIES_COUNT):
            if user.registration_status == RegistrationStatus.Approved:
                break
            time.sleep(SECONDS_BETWEEN_RETRIES)
            user = self.wallet.get_user()
        else:
            raise VaspValidatorError("Filed to create an approved user")

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
        self.wallet.create_payment_command_as_sender(
            reference_id=reference_id,
            vasp_address=vasp_address,
            merchant_name=merchant_name,
            action=action,
            currency=currency,
            amount=amount,
            expiration=expiration,
        )

    def approve_payment_command(self, reference_id):
        self.wallet.approve_payment_command(reference_id)

    def reject_payment_command(self, reference_id):
        self.wallet.reject_payment_command(reference_id)

    def get_payment_details(self, reference_id, vasp_address):
        return self.wallet.get_payment_details(reference_id, vasp_address)

    def prepare_payment_as_receiver(self, action):
        return self.wallet.prepare_payment_as_receiver(action)

    def approve_payment(self, reference_id, init_offchain):
        return self.wallet.approve_payment(reference_id, init_offchain)


def get_random_string(length):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


class VaspValidatorError(Exception):
    ...
