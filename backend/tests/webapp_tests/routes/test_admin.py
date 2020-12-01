# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from flask import Response
from flask.testing import Client

import wallet.services.user
from diem_utils.types.currencies import FiatCurrency
from wallet.services.user import UsersFilter
from wallet.storage import (
    RegistrationStatus,
    User,
)
from wallet.types import UsernameExistsError

NON_UNIQUE_USERNAME = "non_unique"


@pytest.fixture
def get_users_mock(monkeypatch):
    saved = {}

    def get_users(_filter: UsersFilter = UsersFilter.All):
        saved["filter"] = _filter
        saved["users"] = [
            User(
                username="username",
                first_name="bla",
                last_name="blabla",
                is_admin=True,
                registration_status=RegistrationStatus.Approved,
                selected_fiat_currency=FiatCurrency.USD,
                selected_language="en",
                password_salt="123",
                password_hash="deadbeef",
            )
        ]

        return saved["users"]

    monkeypatch.setattr(wallet.services.user, "get_users", get_users)

    yield saved


@pytest.fixture
def create_new_user_mock(monkeypatch):
    saved = {}

    def create_new_user(**kwargs):
        if kwargs["username"] == NON_UNIQUE_USERNAME:
            raise UsernameExistsError(message="")
        saved["params"] = kwargs

        return 1

    monkeypatch.setattr(wallet.services.user, "create_new_user", create_new_user)

    yield saved


class TestAdminGetUsers:
    def test_get_all_users(self, admin_client: Client, get_users_mock) -> None:
        rv: Response = admin_client.get("/admin/users",)
        assert rv.status_code == 200
        users = rv.get_json()["users"]
        assert len(users) == 1
        assert get_users_mock["users"][0].username == users[0]["username"]
        assert get_users_mock["filter"] == UsersFilter.All

    def test_get_admin_users(self, admin_client: Client, get_users_mock) -> None:
        rv: Response = admin_client.get("/admin/users?admin=true",)
        assert rv.status_code == 200
        users = rv.get_json()["users"]
        assert len(users) == 1
        assert get_users_mock["users"][0].username == users[0]["username"]
        assert get_users_mock["filter"] == UsersFilter.Admins

    def test_get_non_admin_users(self, admin_client: Client, get_users_mock) -> None:
        rv: Response = admin_client.get("/admin/users?admin=false",)
        assert rv.status_code == 200
        users = rv.get_json()["users"]
        assert len(users) == 1
        assert get_users_mock["users"][0].username == users[0]["username"]
        assert get_users_mock["filter"] == UsersFilter.NotAdmins

    def test_low_privilege_request(self, authorized_client: Client) -> None:
        rv: Response = authorized_client.get("/admin/users",)
        assert rv.status_code == 403


class TestAdminCreateUsers:
    def test_create_user(self, admin_client: Client, create_new_user_mock) -> None:
        user_params = dict(
            username="test",
            is_admin=True,
            password="qweqwe111",
            first_name="Test",
            last_name="Test oğlu",
        )
        rv: Response = admin_client.post(
            "/admin/users", json=user_params,
        )

        assert rv.status_code == 200
        assert rv.data.decode() == "1"  # user id
        assert create_new_user_mock["params"] == user_params

    def test_non_unique_username(
        self, admin_client: Client, create_new_user_mock
    ) -> None:
        rv: Response = admin_client.post(
            "/admin/users",
            json=dict(
                username=NON_UNIQUE_USERNAME,
                is_admin=True,
                password="qweqwe111",
                first_name="Test",
                last_name="Test oğlu",
            ),
        )

        assert rv.status_code == 409
