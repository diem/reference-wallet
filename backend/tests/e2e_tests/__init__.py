# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import random
import requests
from typing import Callable
from libra_utils.types.currencies import LibraCurrency, FiatCurrency

LRW_WEB_1 = os.getenv("LRW_WEB_1")
LRW_WEB_2 = os.getenv("LRW_WEB_2")
GW_PORT_1 = os.getenv("GW_PORT_1")
GW_PORT_2 = os.getenv("GW_PORT_2")
VASP_ADDR_1 = os.getenv("VASP_ADDR_1")
VASP_ADDR_2 = os.getenv("VASP_ADDR_2")
OFFCHAIN_SERVICE_PORT_1 = os.getenv("OFFCHAIN_SERVICE_PORT_1")
OFFCHAIN_SERVICE_PORT_2 = os.getenv("OFFCHAIN_SERVICE_PORT_2")

print(LRW_WEB_1)
print(LRW_WEB_2)
print(GW_PORT_1)
print(GW_PORT_2)
print(VASP_ADDR_1)
print(VASP_ADDR_2)
print(OFFCHAIN_SERVICE_PORT_1)
print(OFFCHAIN_SERVICE_PORT_2)

sherlock_info = {
    "address_1": "221B Baker Street",
    "address_2": "",
    "city": "London",
    "country": "GB",
    "dob": "1861-06-01",
    "first_name": "Sherlock",
    "last_name": "Holmes",
    "phone": "44 2079460869",
    "selected_fiat_currency": FiatCurrency.USD,
    "selected_language": "en",
    "state": "",
    "zip": "NW1 6XE",
}


def invoke_kyc_check(backend, headers) -> None:
    """Invoke a KYC check by updating user info for the first time"""
    requests.put(f"{backend}/api/user", headers=headers, json=sherlock_info)


def get_test_user_and_auth(backend) -> dict:
    """Create a test user and return auth headers"""
    num = random.randint(0, 1000)
    payload = {"username": f"fakeuser{num}", "password": "fakepassword"}
    res = requests.post(f"{backend}/api/user", json=payload)
    assert res.ok
    token = res.text.strip('"')
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def get_test_payment_method(backend, headers) -> str:
    """
    Create a test payment method and return its id as a string
    NOTE: assumes that this is the only payment method being added for the user
    """
    payment_token = f"paymenttoken{random.randint(0, 1000)}"
    payment_payload = {
        "name": "credit",
        "provider": "CreditCard",
        "token": payment_token,
    }
    payment_post_res = requests.post(
        f"{backend}/api/user/payment-methods", headers=headers, json=payment_payload
    )
    assert payment_post_res.ok

    payment_get_res = requests.get(
        f"{backend}/api/user/payment-methods", headers=headers
    )
    assert payment_get_res.ok
    assert len(payment_get_res.json().get("payment_methods")) > 0
    return str(payment_get_res.json().get("payment_methods")[0].get("id"))


def get_test_quote(backend, headers, amount, buy_sell="buy", pair="LBR_USD") -> str:
    """Creates a test quote and returns its id"""
    quote_payload = {"action": buy_sell, "amount": amount, "currency_pair": pair}
    quote_res = requests.post(
        f"{backend}/api/account/quotes", headers=headers, json=quote_payload
    )
    assert quote_res.ok
    quote_id = quote_res.json().get("quote_id")
    return quote_id


def exec_test_quote(backend, payment_method, quote_id, headers) -> None:
    quote_exec_payload = {"payment_method": payment_method}
    quote_exec_res = requests.post(
        f"{backend}/api/account/quotes/{quote_id}/actions/execute",
        headers=headers,
        json=quote_exec_payload,
    )
    assert quote_exec_res.ok


def get_user_transactions(backend, headers) -> list:
    txn_params = {"limit": 10}
    txns_res = requests.get(
        f"{backend}/api/account/transactions", headers=headers, params=txn_params
    )
    txn_list = txns_res.json().get("transaction_list")
    return txn_list


def get_recv_addr(backend, headers) -> str:
    """Get the receiving subaddr for a test user"""
    addr_res = requests.post(
        f"{backend}/api/account/receiving-addresses", headers=headers
    )
    addr = addr_res.json().get("address")
    return addr


def exec_external_txn(
    backend, headers, recv_addr, amount, currency=LibraCurrency.LBR
) -> None:
    ext_txn_payload = {
        "amount": amount,
        "currency": currency,
        "receiver_address": recv_addr,
    }
    ext_txn_res = requests.post(
        f"{backend}/api/account/transactions", headers=headers, json=ext_txn_payload
    )
    assert ext_txn_res.ok


def get_user_balances(backend, headers) -> list:
    res = requests.get(f"{backend}/api/account", headers=headers)
    balances = res.json().get("balances")
    return balances


def get_balance_from_balances_lst(balances_lst, currency) -> int:
    assert len(balances_lst) > 0
    ret_lst = [b.get("balance") for b in balances_lst if b.get("currency") == currency]
    assert len(ret_lst) == 1  # balance for the currency exists
    return ret_lst[0]


class Doubler:
    def __init__(self, func: Callable[[str], None]) -> None:
        self.func: Callable[[str], None] = func

    def exec(self) -> None:
        self.func(LRW_WEB_1)
        self.func(LRW_WEB_2)
