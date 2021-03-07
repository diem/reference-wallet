# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import context, pytest, typing
from diem import identifier, LocalAccount
from wallet.storage import db_session, User, RegistrationStatus, FiatCurrency, Account
from wallet.services.account import generate_new_subaddress


@pytest.fixture(autouse=True)
def env_context() -> typing.Generator[typing.Any, None, None]:
    context.set(context.from_env())
    yield
    context.set(None)


@pytest.fixture
def random_bech32_address():
    return identifier.encode_account(
        LocalAccount.generate().account_address,
        identifier.gen_subaddress(),
        context.get().config.diem_address_hrp(),
    )


class MyUser:
    def __init__(self):
        self.account_id = self._generate_mock_user().account_id
        self.address = self._generate_my_address(self.account_id)

    @staticmethod
    def _generate_mock_user():
        username = "test_user"

        user = User(
            username=username,
            registration_status=RegistrationStatus.Approved,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
        )
        user.account = Account(name=username)
        db_session.add(user)
        db_session.commit()

        return user

    @staticmethod
    def _generate_my_address(account_id):
        sub_address = generate_new_subaddress(account_id)

        return identifier.encode_account(
            context.get().config.vasp_address,
            sub_address,
            context.get().config.diem_address_hrp(),
        )


@pytest.fixture
def my_user():
    return MyUser()
