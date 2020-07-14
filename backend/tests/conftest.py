# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Generator
from uuid import uuid4

import pytest
from pylibra import FaucetUtils, LibraNetwork

from libra_utils.custody import ProxyTransactionUtils, Custody
from libra_utils.types.liquidity.currency import CurrencyPair
from libra_utils.types.liquidity.lp import LPDetails
from libra_utils.types.liquidity.quote import QuoteId, QuoteData, Rate
from libra_utils.types.liquidity.settlement import DebtData
from libra_utils.types.liquidity.trade import TradeId, TradeData, Direction, TradeStatus
from libra_utils.sdks.liquidity import LpClient
from tests.setup import clear_db
from tests.wallet_tests.pylibra_mocks import (
    FaucetUtilsMock,
    LibraNetworkMock,
    TransactionsMocker,
)
from tests.wallet_tests.services.fx.test_fx import rates
from wallet import services
from wallet.services.transaction import process_incoming_transaction
from wallet.storage import db_session

FAKE_WALLET_PRIVATE_KEY = (
    "682ddb5bcb41abd0a362fe3b332af32a9135abc8effbd75abe8ec6192e2b0c8b"
)
FAKE_WALLET_VASP_ADDR = "9135abc8effbd75abe8ec6192e2b0c8b"
FAKE_LIQUIDITY_PRIVATE_KEY = (
    "e3993257580a98855a5e068c579d06f036f92c7dac37c7b3094f78b2f26b3f00"
)
FAKE_LIQUIDITY_VASP_ADDR = "36f92c7dac37c7b3094f78b2f26b3f00"


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    yield clear_db()
    db_session.remove()


@pytest.fixture(scope="function")
def patch_blockchain(monkeypatch):
    monkeypatch.setattr(FaucetUtils, "mint", FaucetUtilsMock.mint)
    monkeypatch.setattr(LibraNetwork, "getAccount", LibraNetworkMock.get_account)
    monkeypatch.setattr(
        LibraNetwork, "transaction_by_acc_seq", LibraNetworkMock.transaction_by_acc_seq
    )
    monkeypatch.setattr(
        LibraNetwork, "transactions_by_range", LibraNetworkMock.transactions_by_range
    )

    monkeypatch.setattr(
        LibraNetwork, "sendTransaction", LibraNetworkMock.sendTransaction
    )
    monkeypatch.setattr(
        ProxyTransactionUtils,
        "createSignedP2PTransaction",
        TransactionsMocker.create_signed_p2p_transaction,
    )

    yield


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch) -> None:
    def mocked() -> bool:
        return False

    monkeypatch.setattr(services, "run_bg_tasks", mocked)


@pytest.fixture(autouse=True)
def init_test_custody(monkeypatch):
    monkeypatch.setenv("WALLET_CUSTODY_ACCOUNT_NAME", "test_wallet")
    monkeypatch.setenv("LIQUIDITY_CUSTODY_ACCOUNT_NAME", "test_liq")
    monkeypatch.setenv(
        "CUSTODY_PRIVATE_KEYS",
        json.dumps(
            {
                "test_wallet": FAKE_WALLET_PRIVATE_KEY,
                "test_liq": FAKE_LIQUIDITY_PRIVATE_KEY,
            }
        ),
    )

    Custody.init()


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
        libra_deposit_address: Optional[str] = None,
        tx_version: Optional[int] = None,
    ) -> TradeId:
        quote = LpClientMock.QUOTES[quote_id]
        trade_id = TradeId(uuid4())
        if direction == Direction.Buy:
            process_incoming_transaction(
                sender_address="",
                receiver_address=libra_deposit_address,
                sequence=1,
                amount=quote.amount,
                currency=quote.rate.pair.base.value,
                metadata=None,
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
