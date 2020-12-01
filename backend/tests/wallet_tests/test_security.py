# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

from mock import Mock

from wallet import security
from wallet.security import verify_token


def test_verify_token_success(monkeypatch):
    def get_token_mock(token_id):
        mocked_return = Mock()
        mocked_return.user_id = "some_user_id"
        return mocked_return

    monkeypatch.setattr(security, "get_token_id_from_request", lambda: "some_token")
    monkeypatch.setattr(security, "is_valid_token", lambda token_id: True)
    monkeypatch.setattr(
        security, "get_user_by_token", lambda user_id: {"user": "some_user"}
    )
    monkeypatch.setattr(security, "g", Mock())

    func = Mock()

    decorated_func = verify_token(func)

    decorated_func()

    assert func.called


def test_verify_token_invalid_token(monkeypatch):
    monkeypatch.setattr(security, "get_token_id_from_request", lambda: "some_token")
    monkeypatch.setattr(security, "is_valid_token", lambda token_id: False)
    monkeypatch.setattr(security, "revoke_token", lambda token_id: None)

    func = Mock()

    decorated_func = verify_token(func)

    response = decorated_func()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
