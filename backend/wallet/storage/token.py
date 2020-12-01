# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from time import time
from uuid import uuid1

from . import db_session
from .models import Token


def get_token(token_id: str):
    return Token.query.get(token_id)


def create_token(user_id, expiration_time: float) -> str:
    token = Token(user_id=user_id, expiration_time=expiration_time,)
    db_session.add(token)
    db_session.commit()
    return token.id


def delete_token(token_id) -> None:
    token = Token.query.get(token_id)
    if token is not None:
        db_session.delete(token)
        db_session.commit()


def delete_user_tokens(user_id) -> None:
    Token.query.filter_by(user_id=user_id).delete()
    db_session.commit()


def update_token(token_id: uuid1, expiration_time: float) -> None:
    token = Token.query.get(token_id)
    if token is not None:
        token.expiration_time = expiration_time
        db_session.add(token)
        db_session.commit()
