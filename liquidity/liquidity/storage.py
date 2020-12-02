# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
import uuid
from typing import Optional, List

from diem_utils.types.liquidity.errors import AlreadySettled
from diem_utils.types.liquidity.settlement import DebtId
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    Enum,
)

from diem_utils.types.liquidity.currency import CurrencyPairs, Currency, is_fiat
from diem_utils.types.liquidity.quote import QuoteId
from diem_utils.types.liquidity.trade import Direction, TradeStatus, TradeId
from diem_utils.precise_amount import Amount

LpBase = declarative_base(metadata=MetaData())
Session = scoped_session(sessionmaker(autocommit=False, autoflush=False))


class Settlement(LpBase):
    __tablename__ = "settlement"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    debts = relationship("Debt")


class Trade(LpBase):
    __tablename__ = "trade"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    direction = Column(Enum(Direction))
    status = Column(Enum(TradeStatus), default=TradeStatus.Pending)
    tx_version = Column(Integer, nullable=True)

    quote_id = Column(String, ForeignKey("quote.id"))
    quote = relationship("Quote")
    debt_id = Column(String, ForeignKey("debt.id"), nullable=True)
    debt = relationship("Debt")

    def executed(self, tx_version):
        if tx_version is not None:
            self.tx_version = tx_version
        self.status = TradeStatus.Complete
        Session.commit()


class Quote(LpBase):
    __tablename__ = "quote"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    currency_pair = Column(Enum(CurrencyPairs))
    rate = Column(Integer)
    amount = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)


class Debt(LpBase):
    __tablename__ = "debt"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    currency = Column(Enum(Currency))
    amount = Column(BigInteger)  # Positive number - Wallet owes LP
    payment_confirmation = Column(String, nullable=True)

    settlement_id = Column(String, ForeignKey("settlement.id"))
    settlement = relationship("Settlement", back_populates="debts")


DB_URL = os.getenv("LP_DB_URL", "sqlite:////tmp/lp.db")


def configure_storage():
    connect_args = {}
    db_url = DB_URL
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    LpBase.metadata.bind = create_engine(db_url, connect_args=connect_args)


def create_storage():
    LpBase.metadata.create_all()


def reset_storage():
    LpBase.metadata.drop_all()
    LpBase.metadata.create_all()


def create_quote(currency_pair, rate, amount, expires_at) -> Quote:
    quote = Quote(
        currency_pair=currency_pair, rate=rate, amount=amount, expires_at=expires_at,
    )
    Session.add(quote)
    Session.commit()
    return quote


def create_trade(direction, quote_id: QuoteId):
    trade = Trade(direction=direction, quote_id=str(quote_id),)
    Session.add(trade)
    Session.commit()
    return trade


def find_trade(trade_id: TradeId) -> Trade:
    return Session.query(Trade).get(str(trade_id))


def find_quote(quote_id: QuoteId) -> Quote:
    return Session.query(Quote).get(str(quote_id))


def create_new_settlement() -> Settlement:
    trades = Session.query(Trade).filter(Trade.debt_id.is_(None)).all()

    settlement = Settlement(id=str(uuid.uuid4()))
    consolidate_debts(settlement, trades)

    Session.add(settlement)
    Session.commit()
    return settlement


def get_all_unsettled_debts() -> List[Debt]:
    return Session.query(Debt).filter(Debt.payment_confirmation.is_(None)).all()


def settle_debt(debt_id: DebtId, settlement_confirmation: str):
    debt = Session.query(Debt).get(str(str(debt_id)))

    if debt is None:
        raise KeyError(debt_id)
    if debt.payment_confirmation:
        raise AlreadySettled()

    debt.payment_confirmation = settlement_confirmation
    Session.commit()


def trade_to_debt(trade: Trade) -> Optional[Debt]:
    currency_pair = trade.quote.currency_pair.value

    if is_fiat(currency_pair.base) and is_fiat(currency_pair.quote):
        raise AssertionError("Cannot calculate debt for pairs of fiat currencies")

    amount = Amount().deserialize(trade.quote.amount)
    rate = Amount().deserialize(trade.quote.rate)

    # Constants used to change the amount sign
    wallet_owns_lp = Amount().deserialize(1000000)
    lp_owns_wallet = Amount().deserialize(-1000000)

    if is_fiat(currency_pair.quote):
        if trade.direction == Direction.Buy:
            amount *= wallet_owns_lp
        else:
            amount *= lp_owns_wallet
        return Debt(currency=currency_pair.quote, amount=amount.serialize(),)

    if is_fiat(currency_pair.base):
        if trade.direction == Direction.Buy:
            amount /= rate * lp_owns_wallet
        else:
            amount /= rate * wallet_owns_lp
        return Debt(currency=currency_pair.base, amount=amount.serialize(),)

    return None


def consolidate_debts(settlement: Settlement, trades: List[Trade]) -> List[Debt]:
    debts = {}
    for trade in trades:
        debt = trade_to_debt(trade)
        consolidated = debts.setdefault(
            debt.currency,
            Debt(id=str(uuid.uuid4()), currency=debt.currency, amount=0,),
        )
        consolidated.amount += debt.amount
        consolidated.settlement = settlement
        trade.debt_id = consolidated.id

    return [debt for debt in debts.values()]
