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
        data = {
            "base_currency": pair.base.value,
            "quote_currency": pair.quote.value,
            "amount": amount,
        }
        response = requests.post(url=urljoin(self._base_url, "quote"), json=data)
        raise_if_failed(response, f"Failed to get quote for {data}")

        return QuoteData.from_json(response.text)

    def lp_details(self) -> LPDetails:
        response = requests.get(url=urljoin(self._base_url, "details"))
        raise_if_failed(response, "Failed to get Liquidity Provider details")

        return LPDetails.from_json(response.text)

    def trade_info(self, trade_id: TradeId) -> TradeData:
        trade_id_str = str(trade_id)

        response = requests.get(url=urljoin(self._base_url, f"trade/{trade_id_str}"))
        raise_if_failed(response, f"Failed to get info for trade ID {trade_id_str}")

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
        raise_if_failed(response, f"Failed to execute trade for {request_body}")

        return TradeId(UUID(response.json()["trade_id"]))

    def get_debt(self) -> List[DebtData]:
        response = requests.get(url=urljoin(self._base_url, "debt"))
        raise_if_failed(response, "Failed to retrieve debt")

        return [DebtData.from_dict(debt_dict) for debt_dict in response.json()["debts"]]

    def settle(self, debt_id, settlement_confirmation):
        response = requests.put(
            url=urljoin(self._base_url, f"debt/{debt_id}"),
            json={"settlement_confirmation": settlement_confirmation},
        )
        raise_if_failed(response, f"Failed to settle debt ID {debt_id}; "
                                  f"confirmation {settlement_confirmation}")


def raise_if_failed(response, error_description):
    if response.status_code < 200 or response.status_code >= 300:
        raise LpError(f"{error_description} ({response.status_code})")


class LpError(Exception):
    ...
