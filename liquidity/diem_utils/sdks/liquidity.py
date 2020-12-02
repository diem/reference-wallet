# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from http import HTTPStatus
from typing import Optional, List
from urllib.parse import urljoin
from uuid import UUID

import requests

from diem_utils.types.liquidity.currency import CurrencyPair
from diem_utils.types.liquidity.lp import LPDetails
from diem_utils.types.liquidity.quote import QuoteData, QuoteId
from diem_utils.types.liquidity.settlement import DebtData
from diem_utils.types.liquidity.trade import TradeId, Direction, TradeData


class LpClient:
    def __init__(self, base_url=None):
        self._base_url = f"http://{os.getenv('LIQUIDITY_SERVICE_HOST', 'liquidity')}:{os.getenv('LIQUIDITY_SERVICE_PORT', 5000)}"

        if base_url:
            self._base_url = base_url

    def get_quote(self, pair: CurrencyPair, amount: int) -> QuoteData:
        response = requests.post(
            url=urljoin(self._base_url, "quote"),
            json={
                "base_currency": pair.base.value,
                "quote_currency": pair.quote.value,
                "amount": amount,
            },
        )
        response.raise_for_status()
        return QuoteData.from_json(response.text)

    def lp_details(self) -> LPDetails:
        response = requests.get(url=urljoin(self._base_url, "details"))

        if response.status_code != HTTPStatus.OK:
            response.raise_for_status()

        return LPDetails.from_json(response.text)

    def trade_info(self, trade_id: TradeId) -> TradeData:
        trade_id_str = str(trade_id)

        response = requests.get(url=urljoin(self._base_url, f"trade/{trade_id_str}"))
        response.raise_for_status()

        return TradeData.from_json(response.text)

    def trade_and_execute(
        self,
        quote_id: QuoteId,
        direction: Direction,
        diem_deposit_address: Optional[str] = None,
        tx_version: Optional[int] = None,
    ) -> TradeId:
        request_body = {
            "quote_id": str(quote_id),
            "direction": direction.value,
        }

        if diem_deposit_address:
            request_body["diem_deposit_address"] = diem_deposit_address

        if tx_version:
            request_body["tx_version"] = tx_version

        response = requests.post(
            url=urljoin(self._base_url, "trade"), json=request_body
        )
        response.raise_for_status()

        return TradeId(UUID(response.json()["trade_id"]))

    def get_debt(self) -> List[DebtData]:
        response = requests.get(url=urljoin(self._base_url, "debt"))
        response.raise_for_status()

        return [DebtData.from_dict(debt_dict) for debt_dict in response.json()["debts"]]

    def settle(self, debt_id, settlement_confirmation):
        response = requests.put(
            url=urljoin(self._base_url, f"debt/{debt_id}"),
            json={"settlement_confirmation": settlement_confirmation},
        )
        response.raise_for_status()
