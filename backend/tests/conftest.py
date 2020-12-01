# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import context
import inspect
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Generator
from uuid import uuid4

import pytest
from diem.jsonrpc import Client as DiemClient, Transaction, TransactionData
from diem.testnet import Faucet
from diem.txnmetadata import general_metadata
from diem import diem_types, identifier

from diem_utils.types.liquidity.currency import CurrencyPair
from diem_utils.types.liquidity.lp import LPDetails
from diem_utils.types.liquidity.quote import QuoteId, QuoteData, Rate
from diem_utils.types.liquidity.settlement import DebtData
from diem_utils.types.liquidity.trade import TradeId, TradeData, Direction, TradeStatus
from diem_utils.sdks.liquidity import LpClient

from tests.setup import clear_db
from tests.wallet_tests.client_sdk_mocks import (
    FaucetUtilsMock,
    DiemNetworkMock,
    TransactionsMocker,
)
from tests.wallet_tests.services.fx.test_fx import rates
from wallet import services
from wallet.services.transaction import process_incoming_transaction
from wallet.storage import db_session

FAKE_WALLET_PRIVATE_KEY = (
    "682ddb5bcb41abd0a362fe3b332af32a9135abc8effbd75abe8ec6192e2b0c8b"
)
FAKE_WALLET_VASP_ADDR = "c77e1ae3e4a136f070bfcce807747daf"
FAKE_LIQUIDITY_PRIVATE_KEY = (
    "e3993257580a98855a5e068c579d06f036f92c7dac37c7b3094f78b2f26b3f00"
)
FAKE_LIQUIDITY_VASP_ADDR = "36f92c7dac37c7b3094f78b2f26b3f00"


@pytest.fixture(autouse=True)
def env_context():
    yield
    # always clean up global variables for making
    # sure tests won't depend on each other
    context.set(None)


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    yield clear_db()
    db_session.remove()


@pytest.fixture(scope="function")
def patch_blockchain(monkeypatch):
    network = DiemNetworkMock()

    monkeypatch.setattr(Faucet, "mint", FaucetUtilsMock.mint)
    monkeypatch.setattr(DiemClient, "get_account", network.get_account)
    monkeypatch.setattr(
        DiemClient, "get_account_transaction", network.transaction_by_acc_seq
    )
    monkeypatch.setattr(
        DiemClient, "get_account_transactions", network.get_account_transactions,
    )
    monkeypatch.setattr(DiemClient, "get_transactions", network.get_transactions)
    monkeypatch.setattr(DiemClient, "get_events", network.get_events)
    monkeypatch.setattr(DiemClient, "submit", network.sendTransaction)

    def wait_for_transaction(*args):
        return Transaction(version=1, transaction=TransactionData(sequence_number=1))

    monkeypatch.setattr(
        DiemClient, "wait_for_transaction", wait_for_transaction,
    )

    yield network


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch) -> None:
    def mocked() -> bool:
        return False

    monkeypatch.setattr(services, "run_bg_tasks", mocked)


class LpClientMock:
    QUOTES: Dict[QuoteId, QuoteData] = {}
    TRADES: Dict[TradeId, TradeData] = {}

    def get_quote(self, pair: CurrencyPair, amount: int) -> QuoteData:
        rate = Rate(pair=pair, rate=rates[str(pair)])
        quote_id = QuoteId(uuid4())
        quote = QuoteData(
            quote_id=quote_id,
            rate=rate,
            expires_at=datetime.now() + timedelta(minutes=10),
            amount=amount,
        )
        LpClientMock.QUOTES[quote_id] = quote
        return quote

    def lp_details(self) -> LPDetails:
        return LPDetails(
            vasp=FAKE_LIQUIDITY_VASP_ADDR,
            sub_address="d046738b40da0201",
            IBAN_number="123",
        )

    def trade_info(self, trade_id: TradeId) -> TradeData:
        return LpClientMock.TRADES[trade_id]

    def trade_and_execute(
        self,
        quote_id: QuoteId,
        direction: Direction,
        diem_deposit_address: Optional[str] = None,
        tx_version: Optional[int] = None,
    ) -> TradeId:
        quote = LpClientMock.QUOTES[quote_id]
        trade_id = TradeId(uuid4())
        metadata = diem_types.Metadata__Undefined()
        if diem_deposit_address is not None:
            addr, subaddr = identifier.decode_account(diem_deposit_address, "tlb")
            metadata = general_metadata(to_subaddress=subaddr)
        if direction == Direction.Buy:
            process_incoming_transaction(
                sender_address="",
                receiver_address=diem_deposit_address,
                sequence=1,
                amount=quote.amount,
                currency=quote.rate.pair.base.value,
                metadata=metadata,
                blockchain_version=1,
            )

        trade_data = TradeData(
            trade_id=trade_id,
            direction=direction,
            pair=quote.rate.pair,
            amount=quote.amount,
            status=TradeStatus.Complete,
            quote=quote,
            tx_version=1,
        )
        LpClientMock.TRADES[trade_id] = trade_data
        return trade_id

    def get_debt(self) -> List[DebtData]:
        pass


@pytest.fixture(autouse=True)
def mock_lp_client(monkeypatch):
    for name, func in inspect.getmembers(LpClientMock, predicate=inspect.isfunction):
        setattr(LpClient, name, func)
