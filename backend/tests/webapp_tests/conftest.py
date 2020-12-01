# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Generator, Union
from time import time

import pytest, context, typing
from flask.testing import FlaskClient, Client

from wallet.services import user
from wallet.storage import User, Token, Account
from wallet.types import RegistrationStatus
from diem_utils.types.currencies import FiatCurrency
from webapp import app


app.secret_key = "testing"


@pytest.fixture(autouse=True)
def env_context() -> typing.Generator[typing.Any, None, None]:
    context.set(context.from_env())
    yield
    context.set(None)


class UsersService:
    def __init__(self, monkeypatch) -> None:
        self.user_token = "usertoken"
        self.admin_token = "admintoken"
        self.users = {
            self.user_token: {
                "id": 1,
                "is_admin": False,
                "token": Token(user_id=1, expiration_time=time() + 120,),
                "user": User(
                    username="username",
                    registration_status=RegistrationStatus.Approved,
                    selected_fiat_currency=FiatCurrency.USD,
                    selected_language="en",
                    password_hash="fake_password_hash",
                    password_salt="fake_salt",
                    is_admin=False,
                    first_name="Regular",
                    last_name="User",
                    account=Account(name="fake_account"),
                    account_id=1,
                ),
            },
            self.admin_token: {
                "id": 2,
                "is_admin": True,
                "token": Token(user_id=2, expiration_time=time() + 120,),
                "user": User(
                    username="admin",
                    registration_status=RegistrationStatus.Approved,
                    selected_fiat_currency=FiatCurrency.USD,
                    selected_language="en",
                    password_hash="fake_password_hash",
                    password_salt="fake_salt",
                    is_admin=True,
                    first_name="Admin",
                    last_name="User",
                ),
            },
        }

        def mock_is_valid_token(token_id) -> bool:
            return token_id in [self.user_token, self.admin_token]

        def mock_get_user_by_token(token_id) -> Optional[User]:
            if token_id in self.users.keys():
                return self.users[token_id]["user"]
            return None

        monkeypatch.setattr(user, "is_valid_token", mock_is_valid_token)
        monkeypatch.setattr(user, "get_user_by_token", mock_get_user_by_token)

    def get_user_token(self) -> str:
        return self.user_token

    def get_admin_token(self) -> str:
        return self.admin_token


@pytest.fixture
def users_service(monkeypatch) -> UsersService:
    return UsersService(monkeypatch)


@pytest.fixture
def client() -> Generator[Client, None, None]:
    with app.test_client() as client:
        app.before_first_request_funcs = []
        yield client


class AuthorizedClient(FlaskClient):
    def __init__(self, *args, token: Union[str, None] = None, **kwargs,) -> None:
        super().__init__(*args, **kwargs)
        self.token = token

    def open(self, *args, **kwargs):
        if self.token is None:
            return super().open(*args, **kwargs)

        headers = kwargs.get("headers", {})
        if "Authorization" not in headers:
            headers["Authorization"] = "Bearer " + self.token
        kwargs["headers"] = headers

        return super().open(*args, **kwargs)


@pytest.fixture
def authorized_client(users_service: UsersService,) -> Generator[Client, None, None]:
    token = users_service.get_user_token()

    app.test_client_class = AuthorizedClient
    with app.test_client(token=token) as client:
        app.before_first_request_funcs = []
        yield client


@pytest.fixture
def admin_client(users_service: UsersService,) -> Generator[Client, None, None]:
    token = users_service.get_admin_token()

    app.test_client_class = AuthorizedClient

    with app.test_client(token=token) as client:
        app.before_first_request_funcs = []
        yield client
