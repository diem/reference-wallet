# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import hashlib
import os
from enum import Enum
from time import time
from typing import Optional, List
from uuid import uuid4

from diem_utils.types.currencies import FiatCurrency
from wallet import storage
from wallet.config import ADMIN_LOGIN_ENABLED
from wallet.storage import (
    add_user,
    RegistrationStatus,
    get_user,
    User,
    update_user_password,
    get_token,
    update_token,
    create_token,
    PaymentMethod,
)
from wallet.types import LoginError, UsernameExistsError

TOKEN_VALID_TIME: int = 600


class UsersFilter(Enum):
    All = (0,)
    Admins = (1,)
    NotAdmins = 2


def create_new_user(
    username: str,
    password: str,
    is_admin: bool = False,
    first_name: str = "",
    last_name: str = "",
) -> int:
    """
    Attempts to add a new user by username, password hash, and salt, throwing
    types.UsernameExistsError if the username exists already
    """

    if get_user(username=username):
        raise UsernameExistsError(f"username {username} already exists!")

    registration_status = RegistrationStatus.Registered

    if is_admin:
        registration_status = RegistrationStatus.Approved

    password_hash, salt = _generate_password_hash_and_salt(password)

    return add_user(
        username=username,
        password_hash=bytes.hex(password_hash),
        salt=bytes.hex(salt),
        is_admin=is_admin,
        registration_status=registration_status,
        first_name=first_name,
        last_name=last_name,
    )


def update_user(
    user_id: int,
    registration_status: Optional[RegistrationStatus] = None,
    selected_fiat_currency: Optional[FiatCurrency] = None,
    selected_language: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[str] = None,
    phone: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    address_1: Optional[str] = None,
    address_2: Optional[str] = None,
    zip: Optional[str] = None,
) -> User:
    user = storage.update_user(
        user_id=user_id,
        registration_status=registration_status,
        selected_fiat_currency=selected_fiat_currency,
        selected_language=selected_language,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone=phone,
        country=country,
        state=state,
        city=city,
        address_1=address_1,
        address_2=address_2,
        zip=zip,
    )
    return user


def authorize(
    password: str, user: Optional[User] = None, username: Optional[str] = None
) -> LoginError:
    if not user:
        user = get_user(username=username)

    if not user:
        return LoginError.USER_NOT_FOUND

    if user.is_blocked:
        return LoginError.UNAUTHORIZED

    if user.is_admin and not ADMIN_LOGIN_ENABLED:
        return LoginError.ADMIN_DISABLED

    if is_correct_password(user, password):
        return LoginError.SUCCESS
    else:
        return LoginError.WRONG_PASSWORD


def is_correct_password(user: User, password: str):
    password_hash, salt = user.password_hash, user.password_salt
    given_password_hash, _ = _generate_password_hash_and_salt(password, salt)
    return password_hash == bytes.hex(given_password_hash)


def update_password(user_id, new_password):
    password_hash, salt = _generate_password_hash_and_salt(new_password)
    update_user_password(user_id, bytes.hex(password_hash), bytes.hex(salt))


def create_password_reset_token(user: User) -> str:
    token = str(uuid4())
    storage.update_user(user_id=user.id, password_reset_token=token)

    return token


def add_token(user_id: int) -> int:
    expiration_time = time() + TOKEN_VALID_TIME
    token_id = create_token(user_id=user_id, expiration_time=expiration_time)
    return token_id


def is_valid_token(token_id: str) -> bool:
    """
    Token validity needs to be checked every time and session should be extended with every service call.
    """
    token = get_token(token_id)
    if token is None:
        return False
    return time() < token.expiration_time


def get_user_by_reset_token(reset_token: str) -> User:
    return storage.get_user_by_reset_token(token=reset_token)


def get_user_by_token(token_id: str) -> User:
    token = get_token(token_id)
    return get_user(token.user_id)


def revoke_token(token_id: str) -> None:
    storage.delete_token(token_id=token_id)


def extend_token_expiration(token_id) -> None:
    token = get_token(token_id)
    if token is None:
        raise KeyError(token_id)
    new_expiration_time = token.expiration_time + TOKEN_VALID_TIME
    update_token(token_id=token_id, expiration_time=new_expiration_time)


def _generate_password_hash_and_salt(
    password: str, salt: Optional[str] = None
) -> (str, str):
    if not salt:
        salt = os.urandom(32)
    else:
        salt = bytes.fromhex(salt)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 100000
    )

    return password_hash, salt


def get_users(_filter: UsersFilter = UsersFilter.All):
    if _filter == UsersFilter.All:
        return storage.get_all_users()

    return storage.get_users_by_privilege(is_admin=(_filter == UsersFilter.Admins))


def add_payment_method(user_id: str, name: str, provider: str, token: str) -> None:
    storage.add_user_payment_method(user_id, name, provider, token)


def get_payment_methods(user_id: str) -> List[PaymentMethod]:
    return storage.get_payment_methods(user_id=user_id)


def get_user_count():
    return storage.get_user_count(is_admin=False)


def block_user(user_id: int):
    storage.delete_user_tokens(user_id)
    storage.block_user(user_id)
