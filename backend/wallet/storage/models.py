# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    BigInteger,
    Float,
)
from sqlalchemy.orm import relationship
from . import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    password_reset_token = Column(String, nullable=True)
    registration_status = Column(String, nullable=False)
    selected_fiat_currency = Column(String, nullable=False)
    selected_language = Column(String, nullable=False)

    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    phone = Column(String)
    country = Column(String)
    state = Column(String)
    city = Column(String)
    address_1 = Column(String)
    address_2 = Column(String)
    zip = Column(String)

    account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    account = relationship("Account", backref="user", foreign_keys=[account_id])

    payment_methods = relationship("PaymentMethod", backref="user", lazy=True)
    orders = relationship("Order", backref="user", lazy=True)


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    subaddresses = relationship("SubAddress", backref="account", lazy=True)


class SubAddress(Base):
    __tablename__ = "subaddress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String, unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)


class PaymentMethod(Base):
    __tablename__ = "paymentmethod"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    source_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    source_address = Column(String, nullable=True)
    source_subaddress = Column(String, nullable=True)
    destination_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    destination_address = Column(String, nullable=True)
    destination_subaddress = Column(String, nullable=True)
    created_timestamp = Column(DateTime, nullable=False)
    blockchain_version = Column(Integer, nullable=True)
    sequence = Column(Integer, nullable=True)
    logs = relationship("TransactionLog", backref="tx", lazy=True)
    source_account = relationship(
        "Account", backref="sent_transactions", foreign_keys=[source_id]
    )
    destination_account = relationship(
        "Account", backref="received_transactions", foreign_keys=[destination_id]
    )
    off_chain = relationship("OffChain", backref="tx", lazy=True)


# Execution log for transaction
class TransactionLog(Base):
    __tablename__ = "transactionlog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_id = Column(Integer, ForeignKey("transaction.id"), nullable=False)
    log = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)


# Separate global execution log
class ExecutionLog(Base):
    __tablename__ = "executionlog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    log = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class Order(Base):
    __tablename__ = "order"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    amount = Column(BigInteger, nullable=False)
    exchange_amount = Column(BigInteger, nullable=False)
    direction = Column(String, nullable=False)  # Buy/Sell
    base_currency = Column(String, nullable=False)
    quote_currency = Column(String, nullable=False)
    quote_id = Column(String, nullable=True)
    quote_expiration = Column(DateTime, nullable=True)
    order_expiration = Column(DateTime, nullable=False)
    rate = Column(Integer, nullable=True)
    internal_ledger_tx = Column(Integer, ForeignKey("transaction.id"), nullable=True)
    last_update = Column(DateTime, nullable=True)
    order_status = Column(String, nullable=False)
    cover_status = Column(String, nullable=False)
    payment_method = Column(String, nullable=True)
    charge_token = Column(String, nullable=True)
    order_type = Column(String, nullable=False)
    correlated_tx = Column(Integer, ForeignKey("transaction.id"), nullable=True)


class Token(Base):
    __tablename__ = "token"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    expiration_time = Column(Float, nullable=False)


class OffChain(Base):
    __tablename__ = "offchain"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_id = Column(String, nullable=False)
    metadata_signature = Column(String, nullable=True)
    transaction_id = Column(Integer, ForeignKey("transaction.id"), nullable=False)
