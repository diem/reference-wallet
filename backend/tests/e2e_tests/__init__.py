# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import random
import time
import typing
from dataclasses import dataclass

import requests
from diem_utils.types.currencies import FiatCurrency
from requests import HTTPError

LRW_WEB_1 = os.getenv("LRW_WEB_1")
LRW_WEB_2 = os.getenv("LRW_WEB_2")
GW_PORT_1 = os.getenv("GW_PORT_1")
GW_PORT_2 = os.getenv("GW_PORT_2")
VASP_ADDR_1 = os.getenv("VASP_ADDR_1")
VASP_ADDR_2 = os.getenv("VASP_ADDR_2")

print(LRW_WEB_1)
print(LRW_WEB_2)
print(GW_PORT_1)
print(GW_PORT_2)
print(VASP_ADDR_1)
print(VASP_ADDR_2)

SHERLOCK_INFO = {
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


def default_log_fn(*args, **kwargs):
    print(*args, **kwargs)


@dataclass
class UserClient:
    name: str
    backend: str
    token: str
    payment_method: str
    log_fn: typing.Callable

    @staticmethod
    def create(
        backend: str,
        name: str,
        kyc_info=None,
        log_fn=default_log_fn,
    ) -> "UserClient":
        return create_test_user(
            backend,
            name,
            log_fn=log_fn,
            kyc_info=kyc_info,
        )

    def auth_headers(self) -> typing.Dict[str, str]:
        ret = {"Authorization": f"Bearer {self.token}"}
        return ret

    def wait_for_balance(
        self, currency: str, target_balance: int, timeout: int
    ) -> None:
        start_time = time.time()
        max_wait = start_time + timeout
        while time.time() < max_wait:
            new_balance = self.get_balance(currency)
            if new_balance >= target_balance:
                return
            time.sleep(1)

        raise RuntimeError(
            f"wait for {self.name}'s {currency} balance timeout ({timeout} secs), found balance: {new_balance}, expect {target_balance}"
        )

    def update_user(self, user_data: dict) -> dict:
        res = requests.put(
            f"{self.backend}/api/user", headers=self.auth_headers(), json=user_data
        )
        res.raise_for_status()
        return res.json()

    def get_payment_methods(self) -> list:
        res = requests.get(
            f"{self.backend}/api/user/payment-methods", headers=self.auth_headers()
        )
        res.raise_for_status()
        return res.json().get("payment_methods")

    def buy(self, amount: int, currency: str, by_currency: str):
        self.log_fn(f"Buying {amount} {currency} for {self.name} ")
        err = None
        for i in range(8):
            try:
                self._buy(amount, currency, by_currency)
                return
            except Exception as e:
                if isinstance(e, HTTPError):
                    raise
                err = e

        raise RuntimeError(f"failed after retry, last error: {err}")

    def _buy(self, amount: int, currency: str, by_currency: str):
        before_balance = self.get_balance(currency)
        self.log_fn(f"Current balance for {currency}: {amount} for '{self.name}'")
        pair = f"{currency}_{by_currency}"
        quote_id = get_test_quote(
            self.backend, self.auth_headers(), amount, "buy", pair
        )
        self.log_fn(f"quote_id: {quote_id}")
        # pay with the first payment method added to wallet 1
        payload = {"payment_method": self.payment_method}
        res = requests.post(
            f"{self.backend}/api/account/quotes/{quote_id}/actions/execute",
            headers=self.auth_headers(),
            json=payload,
        )
        res.raise_for_status()
        self.wait_for_balance(currency, before_balance + amount, 50)

    def get_recv_addr(self) -> str:
        """Get the receiving subaddr for a test user"""
        res = requests.post(
            f"{self.backend}/api/account/receiving-addresses",
            headers=self.auth_headers(),
        )
        res.raise_for_status()
        return res.json().get("address")

    def transfer(self, addr: str, amount: int, currency: str) -> dict:
        payload = {
            "amount": amount,
            "currency": currency,
            "receiver_address": addr,
        }
        self.log_fn(f"Transferring money '{payload}' for {self.name}")
        res = requests.post(
            f"{self.backend}/api/account/transactions",
            headers=self.auth_headers(),
            json=payload,
        )
        res.raise_for_status()
        return res.json()

    def get_transactions(self) -> list:
        params = {"limit": 10, "sort": "date_desc"}
        res = requests.get(
            f"{self.backend}/api/account/transactions",
            headers=self.auth_headers(),
            params=params,
        )
        res.raise_for_status()
        return res.json().get("transaction_list")

    def get_balances(self) -> typing.List[typing.Dict]:
        res = requests.get(f"{self.backend}/api/account", headers=self.auth_headers())
        res.raise_for_status()
        return res.json().get("balances")

    def create_payment_as_receiver(self):
        res = requests.post(
            f"{self.backend}/api/validation/payment_info/charge",
            headers=self.auth_headers(),
        )
        res.raise_for_status()
        return res.json().get("reference_id"), res.json().get("address")

    def create_payment_as_sender(self, reference_id, vasp_address):
        return self.get_payment_details(reference_id, vasp_address)

    def get_payment_details(self, reference_id, vasp_address):
        res = requests.get(
            f"{self.backend}/api/offchain/query/payment_details?vasp_address={vasp_address}&reference_id={reference_id}",
            headers=self.auth_headers(),
        )
        res.raise_for_status()
        return res.json()

    def approve_payment(self, reference_id):
        payload = {"init_offchain_required": True}

        res = requests.post(
            f"{self.backend}/api/offchain/payment/{reference_id}/actions/approve",
            headers=self.auth_headers(),
            json=payload,
        )
        res.raise_for_status()
        return res.status_code

    def reject_payment(self, reference_id):
        res = requests.post(
            f"{self.backend}/api/offchain/payment/{reference_id}/actions/reject",
            headers=self.auth_headers(),
        )
        res.raise_for_status()

        return res.status_code

    def get_balance(self, currency: str) -> int:
        self.log_fn(f"Getting balance for {currency} for '{self.name}'")
        balances = self.get_balances()
        self.log_fn(f"got balances: {balances} for '{self.name}'")
        for b in balances:
            if b.get("currency") == currency:
                return b.get("balance")

        raise ValueError(f"no balance for the currency {currency} in {balances}")


def randomize_username(name):
    suffix = "@test.com"
    if "@" in name:
        name, suffix = name.split("@")
    return f"{name}_{random.randint(0, 100000000)}{suffix}"


def invoke_kyc_check(backend, headers, kyc_info=None, log_fn=default_log_fn) -> None:
    """Invoke a KYC check by updating user info for the first time"""
    kyc_info = kyc_info or SHERLOCK_INFO
    log_fn(f"Updating user info with KYC for '{kyc_info}'")
    res = requests.put(f"{backend}/api/user", headers=headers, json=kyc_info)
    res.raise_for_status()


def create_test_user(
    backend, username, log_fn=default_log_fn, kyc_info=None
) -> UserClient:
    """Create a test user"""
    username = randomize_username(username)
    payload = {"username": username, "password": "fakepassword"}
    log_fn(f"Creating user '{username}', with password 'fakepassword'")
    res = requests.post(f"{backend}/api/user", json=payload)
    res.raise_for_status()

    token = res.text.strip('"')
    headers = {"Authorization": f"Bearer {token}"}

    invoke_kyc_check(backend, headers, kyc_info=kyc_info, log_fn=log_fn)
    payment_method = create_test_payment_method(backend, headers, log_fn=log_fn)

    return UserClient(
        name=username,
        backend=backend,
        token=token,
        payment_method=payment_method,
        log_fn=log_fn,
    )


def create_test_payment_method(backend, headers, log_fn=default_log_fn) -> str:
    """
    Create a test payment method and return its id as a string
    NOTE: assumes that this is the only payment method being added for the user
    """
    payment_token = f"paymenttoken{random.randint(0, 1000000)}"
    payment_payload = {
        "name": "credit",
        "provider": "CreditCard",
        "token": payment_token,
    }
    log_fn(f"Creating payment method '{payment_payload}'")
    res = requests.post(
        f"{backend}/api/user/payment-methods", headers=headers, json=payment_payload
    )
    res.raise_for_status()

    res = requests.get(f"{backend}/api/user/payment-methods", headers=headers)
    res.raise_for_status()

    assert len(res.json().get("payment_methods")) > 0

    result_id = str(res.json().get("payment_methods")[0].get("id"))
    log_fn(f"Created payment method '{result_id}'")
    return result_id


def get_test_quote(backend, headers, amount, buy_sell="buy", pair="XUS_USD") -> str:
    """Creates a test quote and returns its id"""
    quote_payload = {"action": buy_sell, "amount": amount, "currency_pair": pair}
    quote_res = requests.post(
        f"{backend}/api/account/quotes", headers=headers, json=quote_payload
    )
    quote_res.raise_for_status()
    quote_id = quote_res.json().get("quote_id")
    return quote_id


class Doubler:
    def __init__(self, func: typing.Callable[[str], None]) -> None:
        self.func: typing.Callable[[str], None] = func

    def exec(self) -> None:
        self.func(LRW_WEB_1)
        self.func(LRW_WEB_2)
