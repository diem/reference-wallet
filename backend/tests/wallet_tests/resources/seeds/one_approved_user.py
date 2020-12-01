# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem_utils.types.currencies import FiatCurrency
from wallet.storage import (
    User,
    RegistrationStatus,
    Account,
)


class OneApprovedUser:
    username = "test-user"

    @staticmethod
    def run(db_session):
        user = User(
            username=OneApprovedUser.username,
            registration_status=RegistrationStatus.Approved,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
            account=Account(name="fake_account_seed"),
        )

        db_session.add(user)
        db_session.commit()

        return user.id
