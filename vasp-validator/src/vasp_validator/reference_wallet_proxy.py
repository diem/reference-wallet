#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from typing import List

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


class ReferenceWalletProxy:
    def __init__(self, base_url):
        self.base_url = base_url
        self.authorization_header = {}

    def create_new_user(self, username, password):
        add_user_json = {"username": username, "password": password}
        add_user_response = self._request("POST", "user", json=add_user_json)
        self._set_authorization_token(add_user_response.text)

    def get_user(self):
        user_response = self._request_authorized("GET", "user")
        return User.from_json(user_response.text)

    def update_user(self, user, first_name="Gurki", last_name="Bond"):
        user.first_name = first_name
        user.last_name = last_name
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

    def _request_authorized(self, method, endpoint, json=None):
        response = requests.request(
            method,
            url=f"{self.base_url}/{endpoint}",
            json=json,
            headers=self.authorization_header,
        )
        response.raise_for_status()
        return response
