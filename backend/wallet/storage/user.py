# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import date
from typing import Optional, List

from diem_utils.types.currencies import FiatCurrency
from . import db_session
from .models import User, PaymentMethod
from ..types import RegistrationStatus


def get_user(user_id: Optional[int] = None, username: Optional[str] = None) -> User:
    if user_id:
        return User.query.get(user_id)
    if username:
        return User.query.filter_by(username=username).first()


def add_user(
    username: str,
    password_hash: str,
    salt: str,
    registration_status: RegistrationStatus,
    is_admin: bool = False,
    first_name: str = "",
    last_name: str = "",
) -> int:
    if User.query.filter_by(username=username).first():
        return -1

    user = User(
        username=username,
        registration_status=registration_status,
        selected_fiat_currency=FiatCurrency.USD,
        selected_language="en",
        password_hash=password_hash,
        password_salt=salt,
        is_admin=is_admin,
        first_name=first_name,
        last_name=last_name,
    )
    db_session.add(user)
    db_session.commit()
    return user.id


def get_all_users():
    return User.query.all()


def get_user_count(is_admin):
    return User.query.filter_by(is_admin=is_admin).count()


def get_users_by_privilege(is_admin):
    return User.query.filter_by(is_admin=is_admin)


def is_admin(user_id):
    return User.query.get(user_id).is_admin


def username_exists(username) -> bool:
    return User.query.filter_by(username=username) is not None


def get_user_id(user_name):
    user = User.query.filter_by(username=user_name).first()
    if user is not None:
        return user.id
    else:
        return None


def get_user_by_account_id(account_id: int):
    return User.query.filter_by(account_id=account_id).first()


def get_user_by_reset_token(token: str) -> Optional[User]:
    return User.query.filter_by(password_reset_token=token).first()


def update_user_password(user_id: int, password_hash: str, salt: str) -> None:
    user = User.query.get(user_id)
    if user is not None:
        user.password_hash = password_hash
        user.password_salt = salt
        db_session.commit()
    else:
        raise Exception("User does not exist!")


def update_user(
    user_id: id,
    username: Optional[str] = None,
    registration_status: Optional[RegistrationStatus] = None,
    selected_fiat_currency: Optional[FiatCurrency] = None,
    selected_language: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[date] = None,
    phone: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    address_1: Optional[str] = None,
    address_2: Optional[str] = None,
    zip: Optional[str] = None,
    password_reset_token: Optional[str] = None,
) -> User:
    user = User.query.get(user_id)
    if user is not None:
        for key, value in locals().items():
            if value is not None:
                setattr(user, key, value)

        db_session.commit()
        return user
    else:
        raise Exception("User does not exist!")


def add_user_payment_method(user_id: str, name: str, provider: str, token: str) -> None:
    user = User.query.get(user_id)
    if user is not None:
        user.payment_methods.append(
            PaymentMethod(name=name, provider=provider, token=token)
        )
        db_session.add(user)
        db_session.commit()
    else:
        raise Exception("User does not exist!")


def get_payment_methods(user_id: str) -> List[PaymentMethod]:
    user = User.query.get(user_id)
    if user is not None:
        return user.payment_methods
    else:
        raise Exception("User does not exist!")


def get_user_payment_method(user_id) -> str:
    return "PaymentToken"


def block_user(user_id: int):
    user = User.query.get(user_id)
    if user is None:
        raise KeyError(user_id)
    user.is_blocked = True
    db_session.commit()
