# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus

import pytest
from flask import Response
from flask.testing import Client
from diem_utils.types.currencies import Currencies
from wallet.services import order as order_service
from wallet.storage import Order
from wallet.types import OrderId, Direction


@pytest.fixture
def mock_create_order(monkeypatch):
    def mock(
        user_id: int,
        direction: Direction,
        amount: int,
        base_currency: Currencies,
        quote_currency: Currencies,
    ) -> Order:
        return Order(id="9d2ed500-981b-11ea-bb37-0242ac130002", exchange_amount=12345)

    monkeypatch.setattr(order_service, "create_order", mock)


@pytest.fixture
def mock_process_order(monkeypatch):
    def mock(order_id: OrderId, payment_method) -> None:
        return

    monkeypatch.setattr(order_service, "process_order", mock)


class TestCreateQuote:
    def test_200_usd(self, authorized_client: Client, mock_create_order) -> None:
        rv: Response = authorized_client.post(
            "/account/quotes",
            json=dict(action="buy", amount=10000, currency_pair="Coin1_USD",),
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["price"] == 12345
        assert data["rfq"]["action"] == "buy"

    def test_wrong_action(self, authorized_client: Client) -> None:
        rv: Response = authorized_client.post(
            "/account/quotes",
            json=dict(action="steal", amount=100, currency_pair="Coin1_USD",),
        )
        assert rv.status_code == 400

    def test_illegal_amount(self, authorized_client: Client) -> None:
        rv: Response = authorized_client.post(
            "/account/quotes",
            json=dict(action="buy", amount="what?!", currency_pair="Coin1_USD",),
        )
        assert rv.status_code == 400

    def test_identical_base_quote_currencies(self, authorized_client: Client) -> None:
        rv: Response = authorized_client.post(
            "/account/quotes",
            json=dict(action="buy", amount=1_000_000, currency_pair="Coin1_Coin1"),
        )
        assert rv.status_code == HTTPStatus.BAD_REQUEST


class TestExecuteQuote:
    def test_200(self, authorized_client: Client, mock_process_order) -> None:
        rv: Response = authorized_client.post(
            "/account/quotes/9d2ed500-981b-11ea-bb37-0242ac130002/actions/execute",
            json=dict(payment_method="visa1234"),
        )
        assert rv.status_code == 204


class TestQuoteStatus:
    def test_200(self, authorized_client: Client) -> None:
        rv: Response = authorized_client.get(
            "/account/quotes/9d2ed500-981b-11ea-bb37-0242ac130002",
        )
        assert rv.status_code == 200
