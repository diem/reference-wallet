# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time
import requests
import json
import random
from .. import User, Doubler, LRW_WEB_1, LRW_WEB_2
from libra_utils.types.currencies import LibraCurrency


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
    # create an account on each wallet
    headers1 = get_test_user_and_auth(LRW_WEB_1)
    headers2 = get_test_user_and_auth(LRW_WEB_2)

    invoke_kyc_check(LRW_WEB_1, headers1)
    invoke_kyc_check(LRW_WEB_2, headers2)

    # sleep for KYC check
    time.sleep(10)

    payment_method1 = get_test_payment_method(LRW_WEB_1, headers1)
    get_test_payment_method(LRW_WEB_2, headers2)

    # USD --> Coin1
    starting_amount = 950 * 1_000_000
    quote_id = get_test_quote(
        LRW_WEB_1, headers1, amount=starting_amount, buy_sell="buy", pair="Coin1_USD"
    )

    # pay with the first payment method added to wallet 1
    exec_test_quote(LRW_WEB_1, payment_method1, quote_id, headers1)
    time.sleep(10)

    addr2 = get_recv_addr(LRW_WEB_2, headers2)

    transfer_amount = 800 * 1_000_000
    exec_external_txn(
        LRW_WEB_1, headers1, addr2, transfer_amount, currency=LibraCurrency.Coin1
    )
    time.sleep(10)

    # received
    txns2 = get_user_transactions(LRW_WEB_2, headers2)
    assert len(txns2) > 0
    assert txns2[0].get("amount") == transfer_amount

    # sent
    txns1 = get_user_transactions(LRW_WEB_1, headers1)
    assert len(txns1) > 1  # mint and transfer
    assert any(
        [txn.get("amount") == transfer_amount for txn in txns1]
    )  # txn order not guaranteed

    balances1 = get_user_balances(LRW_WEB_1, headers1)
    coin1_balance1 = get_balance_from_balances_lst(balances1, LibraCurrency.Coin1)
    assert coin1_balance1 == starting_amount - transfer_amount

    balances2 = get_user_balances(LRW_WEB_2, headers2)
    coin1_balance2 = get_balance_from_balances_lst(balances2, LibraCurrency.Coin1)
    assert coin1_balance2 == transfer_amount
