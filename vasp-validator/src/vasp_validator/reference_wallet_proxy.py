#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from typing import List, Callable, Optional

import requests

from .models import (
    User,
    Address,
    Transaction,
    Transactions,
    RequestForQuote,
    Quote,
    CreateTransaction,
    AccountInfo,
    OffChainSequenceInfo,
    TransactionId,
    FundsTransfer,
    PaymentDetails,
    PreparePaymentInfoResponse,
)
from .models_fppa import (
    FundPullPreApprovalScope,
    FundsPullPreApprovalRequest,
    FundsPullPreApproval,
    FundPullPreApprovalStatus,
)

RequestSender = Callable[[str, str, Optional[dict]], requests.Response]


class ReferenceWalletProxy:
    def __init__(self, base_url):
        self.base_url = base_url
        self.authorization_header = {}
        self.funds_pull_preapproval = ReferenceWalletProxyFPPA(self._request_authorized)

    def create_new_user(self, username, password):
        add_user_json = {"username": username, "password": password}
        add_user_response = self._request("POST", "user", json=add_user_json)
        self._set_authorization_token(add_user_response.text)

    def get_user(self):
        user_response = self._request_authorized("GET", "user")
        return User.from_json(user_response.text)

    def update_user(self, user: User):
        self._request_authorized("PUT", "user", json=user.to_dict())
        return self.get_user()

    def get_account_info(self) -> AccountInfo:
        response = self._request_authorized("GET", "account")
        return AccountInfo.from_json(response.text)

    def get_balance(self, currency):
        return sum(
            x.balance
            for x in self.get_account_info().balances
            if x.currency == currency
        )

    def get_receiving_address(self) -> str:
        address_response = self._request_authorized(
            "POST", "account/receiving-addresses"
        )
        address = Address.from_json(address_response.text)
        return address.address

    def get_transaction_list(self) -> List[Transaction]:
        account_transactions_response = self._request_authorized(
            "GET", "account/transactions"
        )
        transactions = Transactions.from_json(account_transactions_response.text)
        return transactions.transaction_list

    def create_deposit_quote(self, amount: int, currency_pair) -> Quote:
        quote_request = RequestForQuote(
            action="buy",
            amount=amount,
            currency_pair=currency_pair,
        )
        quote_response = self._request_authorized(
            "POST", "account/quotes", json=quote_request.to_dict()
        )
        return Quote.from_json(quote_response.text)

    def execute_quote(self, quote_id: str):
        self._request_authorized(
            "POST", f"account/quotes/{quote_id}/actions/execute", json={}
        )

    def get_offchain_state(self, reference_id) -> OffChainSequenceInfo:
        # TBD: There is no way, at the moment, to get off-chain sequence
        #      state. Should be implemented.
        return OffChainSequenceInfo()

    def send_transaction(self, address, amount, currency) -> TransactionId:
        tx_request = CreateTransaction(
            currency=currency,
            amount=amount,
            receiver_address=address,
        )
        send_transaction_response = self._request_authorized(
            "POST", "account/transactions", json=tx_request.to_dict()
        )
        return TransactionId.from_json(send_transaction_response.text)

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
        request = {
            "reference_id": reference_id,
            "vasp_address": vasp_address,
            "merchant_name": merchant_name,
            "action": action,
            "currency": currency,
            "amount": amount,
            "expiration": expiration,
        }

        self._request_authorized("POST", "offchain/payment_command", json=request)

    def get_payment_details(self, reference_id, vasp_address) -> PaymentDetails:
        response = self._request_authorized(
            "GET",
            f"offchain/query/payment_details?"
            f"vasp_address={vasp_address}&"
            f"reference_id={reference_id}",
        )

        return PaymentDetails.from_json(response.text) if response.text else None

    def prepare_payment_as_receiver(self, action: str = "charge") -> (str, str):
        response = self._request_authorized(
            "POST", f"/validation/payment_info/{action}"
        )
        response_object = PreparePaymentInfoResponse.from_json(response.text)

        return response_object.reference_id, response_object.address

    def approve_payment(self, reference_id: str, init_offchain: bool):
        self._request_authorized(
            "POST",
            f"/offchain/payment/{reference_id}/actions/approve",
            json={"init_offchain_required": init_offchain},
        )

    def approve_payment_command(self, reference_id):
        self._request_authorized(
            "POST", f"/offchain/payment_command/{reference_id}/actions/approve"
        )

    def reject_payment_command(self, reference_id):
        self._request_authorized(
            "POST", f"/offchain/payment_command/{reference_id}/actions/reject"
        )

    def get_transaction(self, tx_id) -> FundsTransfer:
        response = self._request_authorized("GET", f"account/transactions/{tx_id}")
        return FundsTransfer.from_json(response.text)

    def _set_authorization_token(self, token):
        self.authorization_header = {"Authorization": "Bearer " + token}

    def _request(self, method, endpoint, json=None):
        response = requests.request(
            method, url=f"{self.base_url}/{endpoint}", json=json
        )
        response.raise_for_status()
        return response

    def _request_authorized(self, method, endpoint, json=None) -> requests.Response:
        response = requests.request(
            method,
            url=f"{self.base_url}/{endpoint}",
            json=json,
            headers=self.authorization_header,
        )
        response.raise_for_status()
        return response


class ReferenceWalletProxyFPPA:
    """
    Sends to the reference wallet funds pull pre-approval related requests.
    """

    def __init__(self, request_wallet_authorized: RequestSender):
        self._request_authorized = request_wallet_authorized

    def get_all_preapprovals(self) -> List[FundsPullPreApproval]:
        r = self._request_authorized("GET", "offchain/funds_pull_pre_approvals")
        preapprovals = r.json()
        return [
            FundsPullPreApproval.from_dict(x)
            for x in preapprovals["funds_pull_pre_approvals"]
        ]

    def request_preapproval_from_another(
        self,
        payer_addr_bech32: str,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        fppa_request = FundsPullPreApprovalRequest(
            payer_address=payer_addr_bech32,
            description=description,
            scope=scope,
        )
        r = self._request_authorized(
            "POST", "validation/funds_pull_pre_approvals", fppa_request.to_dict()
        )
        return r.json()["funds_pull_pre_approval_id"]

    def create_fppa_request_for_unknown_payer(
        self,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> (str, str):
        r = self._request_authorized(
            "POST",
            "validation/funds_pull_pre_approvals",
            {"description": description, "scope": scope.to_dict()},
        )
        return r.json()["funds_pull_pre_approval_id"], r.json()["address"]

    def update_preapproval_status(
        self, fppa_id: str, status: FundPullPreApprovalStatus
    ):
        self._request_authorized(
            "PUT",
            f"offchain/funds_pull_pre_approvals/{fppa_id}",
            {"status": status.value},
        )

    def create_and_approve(
        self,
        biller_address: str,
        funds_pull_pre_approval_id: str,
        scope: FundPullPreApprovalScope,
        description: str,
    ):
        self._request_authorized(
            "POST",
            "offchain/funds_pull_pre_approvals",
            {
                "biller_address": biller_address,
                "funds_pull_pre_approval_id": funds_pull_pre_approval_id,
                "scope": scope.to_dict(),
                "description": description,
            },
        )
