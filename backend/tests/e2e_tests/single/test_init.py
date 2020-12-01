# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time
import requests
import json
import random
from .. import *


def test_init() -> None:
    # just test that the webapp works
    res = requests.get(f"{LRW_WEB_1}/api/execution_logs")
    assert res.ok


def test_create_account() -> None:
    num = random.randint(0, 1000)
    payload = {"username": f"fakeuser{num}", "password": "fakepassword"}
    res = requests.post(f"{LRW_WEB_1}/api/user", json=payload)
    assert res.ok
    token = res.text.strip('"')
    headers = {"Authorization": f"Bearer {token}"}
    users_res = requests.get(f"{LRW_WEB_1}/api/user", headers=headers)
    assert users_res.ok
    user = json.loads(users_res.text)
    assert user.get("username") == payload.get("username")
