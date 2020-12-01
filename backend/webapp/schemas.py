# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from itertools import chain

from marshmallow import Schema, fields
from marshmallow.validate import OneOf, Range

from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from wallet.types import TransactionDirection, TransactionStatus

SUPPORTED_CONVERSIONS = [
    f"{base}_{quote}"
    for base in DiemCurrency
    for quote in chain(list(FiatCurrency.__members__), list(DiemCurrency.__members__))
]


def diem_amount_field(**kwargs) -> fields.Field:
    """Defines Diem amount schema field"""
    return fields.Int(
        description="Amount of microdiems",
        validate=Range(min=0),
        strict=True,
        **kwargs,
    )


def fiat_amount_field(**kwargs) -> fields.Field:
    """Defines fiat currency amount schema field"""
    return fields.Int(
        description="Amount of fiat currency in scale factor 6",
        validate=Range(min=1),
        strict=True,
        **kwargs,
    )


def fiat_currency_code_field(**kwargs) -> fields.Field:
    """Defines fiat currency code schema field"""
    return fields.Str(
        description="Fiat currency code",
        validate=OneOf(list(FiatCurrency.__members__)),
        **kwargs,
    )


def diem_currency_code_field(**kwargs) -> fields.Field:
    """Defines Diem currency code schema field"""
    return fields.Str(
        description="Diem currency code",
        validate=OneOf(list(DiemCurrency.__members__)),
        **kwargs,
    )


def transaction_direction_field(**kwargs) -> fields.Field:
    """Defines Diem currency code schema field"""
    return fields.Str(
        description="Transaction direction",
        validate=OneOf([td.lower() for td in list(TransactionDirection.__members__)]),
        **kwargs,
    )


def transaction_status_field(**kwargs) -> fields.Field:
    """Defines Diem currency code schema field"""
    return fields.Str(
        description="Transaction status",
        validate=OneOf([ts.lower() for ts in list(TransactionStatus.__members__)]),
        **kwargs,
    )


def currency_pair_field(**kwargs) -> fields.Field:
    """Defines currency pair schema field"""
    return fields.Str(
        description="Defines bought and sold currencies. "
        "Has the form `<base currency>_<counter currency>`",
        validate=OneOf(SUPPORTED_CONVERSIONS),
        **kwargs,
    )


class RequestForQuote(Schema):
    action = fields.Str(required=True, validate=OneOf(["buy", "sell"]))
    amount = diem_amount_field(required=True)
    currency_pair = currency_pair_field(required=True)


class Quote(Schema):
    quote_id = fields.Str(required=True)
    rfq = fields.Nested(RequestForQuote, required=True)
    price = diem_amount_field(required=True)
    expiration_time = fields.DateTime(required=True)


class QuoteStatus(Schema):
    status = fields.Str(required=True, validate=OneOf(["Pending", "Success", "Failed"]))


class QuoteExecution(Schema):
    payment_method = fields.Str(required=False, allow_none=True, missing=None)


class Rate(Schema):
    currency_pair = currency_pair_field(required=True)
    price = diem_amount_field(required=True)


class RateResponse(Schema):
    rates = fields.List(fields.Nested(Rate))


class User(Schema):
    username = fields.Str(required=True)
    registration_status = fields.Str(required=True)
    is_admin = fields.Bool(required=True)

    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)


class Users(Schema):
    users = fields.List(fields.Nested(User))


class UserCreationRequest(Schema):
    username = fields.Str(required=True)
    is_admin = fields.Bool(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    password = fields.Str(required=True)


class Debt(Schema):
    debt_id = fields.Str(required=True)
    currency = fiat_currency_code_field(required=True)
    amount = fiat_amount_field(required=True)


class PendingSettlement(Schema):
    debt = fields.List(fields.Nested(Debt))


class DebtSettlement(Schema):
    settlement_confirmation = fields.Str(required=True)


class Balance(Schema):
    currency = diem_currency_code_field(required=True)
    balance = diem_amount_field(required=True)


class Balances(Schema):
    balances = fields.List(fields.Nested(Balance), required=True)


class UserAddress(Schema):
    user_id = fields.Str(required=False, allow_none=True)
    vasp_name = fields.Str(required=False, allow_none=True)
    full_addr = fields.Str(required=False, allow_none=True)


class BlockchainTransaction(Schema):
    amount = diem_amount_field()
    status = fields.Str()
    source = fields.Str(allow_none=True)
    destination = fields.Str(allow_none=True)
    expirationTime = fields.Str(allow_none=True)
    sequenceNumber = fields.Int(allow_none=True)
    version = fields.Int(allow_none=True)


class Transaction(Schema):
    id = fields.Int(required=True)
    amount = diem_amount_field(required=True)
    currency = diem_currency_code_field(required=True)
    direction = transaction_direction_field(required=True)
    status = transaction_status_field(required=True)
    timestamp = fields.Str(required=True)
    source = fields.Nested(UserAddress)
    destination = fields.Nested(UserAddress)
    blockchain_tx = fields.Nested(
        BlockchainTransaction, required=False, allow_none=True
    )


class CreateTransaction(Schema):
    currency = diem_currency_code_field(required=True)
    amount = diem_amount_field(required=True)
    receiver_address = fields.Str(required=True)


class AccountTransactions(Schema):
    transaction_list = fields.List(fields.Nested(Transaction))


class FullAddress(Schema):
    address = fields.Str(required=True)


class Error(Schema):
    error = fields.Str(required=True)
    code = fields.Int(required=True)


class TotalUsers(Schema):
    user_count = fields.Int(required=True)


class Chain(Schema):
    chain_id = fields.Int(required=True)
    display_name = fields.Str(required=True)
