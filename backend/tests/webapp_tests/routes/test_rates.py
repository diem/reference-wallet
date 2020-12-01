# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from flask import Response
from flask.testing import Client


class TestGetRates:
    def test_200(self, authorized_client: Client) -> None:
        res: Response = authorized_client.get("/account/rates")
        data = res.get_json()
        assert res.status_code == 200
        assert data["rates"]
