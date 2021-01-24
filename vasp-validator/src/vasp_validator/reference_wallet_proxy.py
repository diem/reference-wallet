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

    def send_transaction(self, address, amount, currency) -> Transaction:
        tx_request = CreateTransaction(
            currency=currency,
            amount=amount,
            receiver_address=address,
        )
        send_transaction_response = self._request_authorized(
            "POST", "account/transactions", json=tx_request.to_dict()
        )
        return Transaction.from_json(send_transaction_response.text)

    def get_transaction(self, tx_id) -> Transaction:
        response = self._request_authorized("GET", f"account/transactions/{tx_id}")
        return Transaction.from_json(response.text)

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

    def update_preapproval_status(
        self, fppa_id: str, status: FundPullPreApprovalStatus
    ):
        self._request_authorized(
            "PUT",
            f"offchain/funds_pull_pre_approvals/{fppa_id}",
            {"status": status.value},
        )
