# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os, time, typing
import random
import requests
from dataclasses import dataclass
from diem_utils.types.currencies import DiemCurrency, FiatCurrency

LRW_WEB_1 = os.getenv("LRW_WEB_1")
LRW_WEB_2 = os.getenv("LRW_WEB_2")
GW_PORT_1 = os.getenv("GW_PORT_1")
GW_PORT_2 = os.getenv("GW_PORT_2")
VASP_ADDR_1 = os.getenv("VASP_ADDR_1")
VASP_ADDR_2 = os.getenv("VASP_ADDR_2")
GW_OFFCHAIN_SERVICE_PORT_1 = os.getenv("GW_OFFCHAIN_SERVICE_PORT_1")
GW_OFFCHAIN_SERVICE_PORT_2 = os.getenv("GW_OFFCHAIN_SERVICE_PORT_2")

print(LRW_WEB_1)
print(LRW_WEB_2)
print(GW_PORT_1)
print(GW_PORT_2)
print(VASP_ADDR_1)
print(VASP_ADDR_2)
print(GW_OFFCHAIN_SERVICE_PORT_1)
print(GW_OFFCHAIN_SERVICE_PORT_2)

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


@dataclass
class UserClient:
    name: str
    backend: str
    token: str
    payment_method: str

    @staticmethod
    def create(backend: str, name: str) -> "UserClient":
        return create_test_user(backend, f"{name}_{random.randint(0, 1000)}")

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

    def buy(self, amount: int, currency: str, by_currency: str):
        err = None
        for i in range(3):
            try:
                self._buy(amount, currency, by_currency)
                return
            except Exception as e:
                err = e
                pass

        raise RuntimeError(f"failed after retry, last error: {e}")

    def _buy(self, amount: int, currency: str, by_currency: str):
        before_balance = self.get_balance(currency)

        pair = f"{currency}_{by_currency}"
        quote_id = get_test_quote(
            self.backend, self.auth_headers(), amount, "buy", pair
        )
        print(f"quote_id: {quote_id}")
        # pay with the first payment method added to wallet 1
        payload = {"payment_method": self.payment_method}
        res = requests.post(
            f"{self.backend}/api/account/quotes/{quote_id}/actions/execute",
            headers=self.auth_headers(),
            json=payload,
        )
        res.raise_for_status()
        self.wait_for_balance(currency, before_balance + amount, 20)

    def get_recv_addr(self) -> str:
        """Get the receiving subaddr for a test user"""
        res = requests.post(
            f"{self.backend}/api/account/receiving-addresses",
            headers=self.auth_headers(),
        )
        res.raise_for_status()
        return res.json().get("address")

    def transfer(self, addr: str, amount: int, currency) -> None:
        payload = {
            "amount": amount,
            "currency": currency,
            "receiver_address": addr,
        }
        res = requests.post(
            f"{self.backend}/api/account/transactions",
            headers=self.auth_headers(),
            json=payload,
        )
        res.raise_for_status()

    def get_transactions(self) -> list:
        params = {"limit": 10}
        res = requests.get(
            f"{self.backend}/api/account/transactions",
            headers=self.auth_headers(),
            params=params,
        )
        res.raise_for_status()
        return res.json().get("transaction_list")

    def get_balance(self, currency: str) -> list:
        res = requests.get(f"{self.backend}/api/account", headers=self.auth_headers())
        res.raise_for_status()
        balances = res.json().get("balances")
        for b in balances:
            if b.get("currency") == currency:
                return b.get("balance")

        raise ValueError(f"no balance for the currency {currency} in {balances}")


def invoke_kyc_check(backend, headers) -> None:
    """Invoke a KYC check by updating user info for the first time"""

    res = requests.put(f"{backend}/api/user", headers=headers, json=sherlock_info)
    res.raise_for_status()


def create_test_user(backend, username) -> UserClient:
    """Create a test user"""

    payload = {"username": username, "password": "fakepassword"}
    res = requests.post(f"{backend}/api/user", json=payload)
    res.raise_for_status()

    token = res.text.strip('"')
    headers = {"Authorization": f"Bearer {token}"}

    invoke_kyc_check(backend, headers)
    payment_method = create_test_payment_method(backend, headers)

    return UserClient(
        name=username, backend=backend, token=token, payment_method=payment_method
    )


def create_test_payment_method(backend, headers) -> str:
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
    res = requests.post(
        f"{backend}/api/user/payment-methods", headers=headers, json=payment_payload
    )
    res.raise_for_status()

    res = requests.get(f"{backend}/api/user/payment-methods", headers=headers)
    res.raise_for_status()

    assert len(res.json().get("payment_methods")) > 0
    return str(res.json().get("payment_methods")[0].get("id"))


def get_test_quote(backend, headers, amount, buy_sell="buy", pair="Coin1_USD") -> str:
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
