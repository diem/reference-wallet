# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from . import db_session, get_user
from .models import Account, SubAddress


def create_account(account_name: str, user_id: Optional[int] = None) -> Account:
    account = Account(name=account_name)
    if user_id:
        user = get_user(user_id)
        user.account = account
        db_session.add(user)
    else:
        db_session.add(account)

    db_session.commit()
    return account


def get_account(
    account_id: Optional[int] = None, account_name: Optional[str] = None
) -> Optional[Account]:
    if account_id:
        return Account.query.filter_by(id=account_id).first()
    if account_name:
        return Account.query.filter_by(name=account_name).first()
    return None


def get_account_id_from_subaddr(subaddr: str) -> Optional[int]:
    subaddr_record = SubAddress.query.filter_by(address=subaddr).first()
    return subaddr_record.account_id if subaddr_record else None


def add_subaddress(account_id: int, subaddr: str) -> str:
    account = Account.query.get(account_id)
    account.subaddresses.append(SubAddress(address=subaddr))
    db_session.add(account)
    db_session.commit()
    return subaddr


def is_subaddress_exists(subaddr: str) -> bool:
    return SubAddress.query.filter(SubAddress.address == subaddr).first()
