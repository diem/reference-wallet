# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services import account as account_service
from wallet.storage import db_session, User


def test_account_viewable_by_same_user():
    account_name = "test_account"
    user = OneUser.run(db_session, account_name=account_name)

    assert account_service.is_user_allowed_for_account(
        account_name=account_name, user=user
    )


def test_account_not_viewable_by_other_user():
    account_name1 = "test_account"
    user = OneUser.run(db_session, account_name=account_name1, username="user1")

    account_name2 = "test_account2"
    user2 = OneUser.run(db_session, account_name=account_name2, username="user2")

    assert not account_service.is_user_allowed_for_account(
        account_name=account_name1, user=user2
    )


def test_account_viewable_by_admin():
    account_name = "test_account"
    user = User(id=1, is_admin=True)

    assert account_service.is_user_allowed_for_account(
        account_name=account_name, user=user
    )
