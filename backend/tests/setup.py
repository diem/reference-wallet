# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from wallet.storage import db_session, engine, Base
from wallet.storage.models import User, Account
from wallet.types import RegistrationStatus
from diem_utils.types.currencies import FiatCurrency


def clear_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def setup_fake_data() -> None:
    clear_db()

    fake_users = [
        User(
            username="sunmi",
            registration_status=RegistrationStatus.Registered,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
            is_admin=True,
            first_name="First1",
            last_name="Last1",
            account=Account(),
        ),
        User(
            username="sunyc",
            registration_status=RegistrationStatus.Registered,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
            is_admin=False,
            first_name="First2",
            last_name="Last2",
            account=Account(),
        ),
        User(
            username="rustie",
            registration_status=RegistrationStatus.Registered,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
            is_admin=False,
            first_name="First3",
            last_name="Last3",
            account=Account(),
        ),
    ]

    for user in fake_users:
        db_session.add(user)

    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        db_session.flush()
