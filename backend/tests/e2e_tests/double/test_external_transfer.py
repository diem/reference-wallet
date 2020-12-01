# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import requests
import json
import random
from .. import UserClient, Doubler, LRW_WEB_1, LRW_WEB_2


def test_init() -> None:
    # just test that the webapp works
    def get_logs(backend):
        res = requests.get(f"{backend}/api/execution_logs")
        assert res.ok

    Doubler(get_logs).exec()


def test_create_account() -> None:
    def create_account(backend):
        num = random.randint(0, 1000)
        payload = {"username": f"fakeuser{num}", "password": "fakepassword"}
        res = requests.post(f"{backend}/api/user", json=payload)
        assert res.ok
        token = res.text.strip('"')
        headers = {"Authorization": f"Bearer {token}"}
        users_res = requests.get(f"{backend}/api/user", headers=headers)
        assert users_res.ok
        user = json.loads(users_res.text)
        assert user.get("username") == payload.get("username")

    Doubler(create_account).exec()


def test_external_transfer() -> None:
    """
    Test an external transfer of Coin1 from VASP1 to VASP2
    """

    currency = "Coin1"
    user1 = UserClient.create(LRW_WEB_1, "transfer_test_user1")
    user2 = UserClient.create(LRW_WEB_2, "transfer_test_user2")
    user1.buy(9_000_000, currency, "USD")

    transfer(user1, user2, 1_000_000, currency)


def test_external_transfer_requires_offchain() -> None:
    """
    Test an external transfer of Coin1 from VASP1 to VASP2
    """

    currency = "Coin1"
    user1 = UserClient.create(LRW_WEB_1, "offchain_test_user1")
    user2 = UserClient.create(LRW_WEB_2, "offchain_test_user2")

    # under threshold of travel rule to buy enough coins for test
    user1.buy(600_000_000, currency, "USD")
    user1.buy(600_000_000, currency, "USD")

    transfer(user1, user2, 1_100 * 1_000_000, currency)


def transfer(user1: UserClient, user2: UserClient, transfer_amount: int, currency: str):
    user1_balance_before_transfer = user1.get_balance(currency)

    addr2 = user2.get_recv_addr()
    user1.transfer(addr2, transfer_amount, currency)

    # sent
    user1.wait_for_balance(
        currency, user1_balance_before_transfer - transfer_amount, 20
    )
    sent_txns = [
        txn for txn in user1.get_transactions() if txn.get("direction") == "sent"
    ]

    assert len(sent_txns) == 1
    assert sent_txns[0].get("amount") == transfer_amount

    user2.wait_for_balance(currency, transfer_amount, 20)
    # received
    txns2 = user2.get_transactions()
    assert len(txns2) == 1
    assert txns2[0].get("amount") == transfer_amount
