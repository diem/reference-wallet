# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time
import requests
import json
import random
from .. import Doubler


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
