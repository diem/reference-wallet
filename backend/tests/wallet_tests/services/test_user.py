# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import date
from typing import List

import pytest

from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet import types
from wallet.services import user as user_service
from wallet.services.kyc import is_verified, process_user_kyc
from wallet.services.user import create_new_user, authorize, update_password
from wallet.storage import db_session
from wallet.types import RegistrationStatus, UsernameExistsError


def test_create_user() -> None:
    username = "fakeuserid"
    password = "supersecurepassword"
    create_new_user(username, password)

    assert authorize(username=username, password=password)


def test_update_user_password() -> None:
    username = "fakeuserid"
    password = "supersecurepassword"
    user_id = create_new_user(username, password)

    password2 = "updatedsupersecurepassword"
    update_password(user_id, password2)

    assert (
        authorize(username=username, password=password)
        == types.LoginError.WRONG_PASSWORD
    )
    assert authorize(username=username, password=password2) == types.LoginError.SUCCESS


def test_create_existing_user_fails() -> None:
    username = "fakeuserid"
    password = "supersecurepassword"
    create_new_user(username, password)

    with pytest.raises(UsernameExistsError):
        create_new_user(username, password)


def test_approved_user_is_verified() -> None:
    user = OneUser.run(db_session, registration_status=RegistrationStatus.Approved)

    assert is_verified(user.id)


def test_not_approved_user_is_not_verified() -> None:
    user = OneUser.run(db_session, registration_status=RegistrationStatus.Pending)
    assert not is_verified(user.id)


def test_kyc_started_user_pending(monkeypatch) -> None:
    status_updates: List[RegistrationStatus] = []

    def update_user_mock(
        user_id: id, registration_status: RegistrationStatus, **kwargs
    ):
        status_updates.append(registration_status)

    monkeypatch.setattr(user_service, "update_user", update_user_mock)

    user = OneUser.run(db_session, registration_status=RegistrationStatus.Registered)
    process_user_kyc(
        user.id,
        selected_fiat_currency="USD",
        selected_language="en",
        first_name="test_first_name",
        last_name="test_last_name",
        dob=date.fromisoformat("1980-01-01"),
        phone="123456789",
        country="NY",
        state="NY",
        address_1="123 test address",
        zip="12345",
    )

    assert status_updates == [RegistrationStatus.Pending, RegistrationStatus.Approved]
