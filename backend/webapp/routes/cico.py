# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Cash-in/cash-out endpoints"""

# pyre-ignore-all-errors[15]

from datetime import datetime
from http import HTTPStatus
from uuid import UUID

from flask import Blueprint, request
from itertools import chain

from diem_utils.precise_amount import Amount
from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from diem_utils.types.liquidity.currency import Currency
from wallet.services import order as order_service
from wallet.services.fx.fx import get_rate
from wallet.types import OrderId, Direction
from webapp.schemas import (
    RequestForQuote,
    Quote,
    QuoteStatus,
    QuoteExecution,
    RateResponse,
    Error,
)
from .strict_schema_view import (
    StrictSchemaView,
    response_definition,
    body_parameter,
    path_uuid_param,
)

cico = Blueprint("cico", __name__)


class CicoRoutes:
    class CicoView(StrictSchemaView):
        tags = ["CICO"]

    class CreateQuoteView(CicoView):
        summary = "Request a new quote"
        parameters = [
            body_parameter(RequestForQuote),
        ]
        responses = {
            HTTPStatus.OK: response_definition("A new quote", schema=Quote),
            HTTPStatus.BAD_REQUEST: response_definition(
                "Same base and quote currency is not allowed", schema=Error
            ),
        }

        def post(self):
            rfq = request.json

            base_currency, quote_currency = rfq["currency_pair"].split("_")
            amount = int(rfq["amount"])
            rfq_action: str = rfq["action"]

            order_direction = Direction[rfq_action.capitalize()]

            if base_currency == quote_currency:
                return self.respond_with_error(
                    HTTPStatus.BAD_REQUEST,
                    f"Converting currency {base_currency} to itself is impossible",
                )

            order = order_service.create_order(
                user_id=self.user.id,
                direction=order_direction,
                amount=amount,
                base_currency=Currency[base_currency],
                quote_currency=Currency[quote_currency],
            )

            quote = {
                "quote_id": order.id,
                "rfq": rfq,
                "price": order.exchange_amount,
                "expiration_time": datetime.now(),
            }
            return quote, HTTPStatus.OK

    class GetQuoteStatusView(CicoView):
        summary = "Get quote execution status"
        parameters = [
            path_uuid_param("quote_id", "ID of an existing quote"),
        ]
        responses = {
            HTTPStatus.OK: response_definition("Quote status", schema=QuoteStatus)
        }

        def get(self, quote_id: str):
            # TODO
            return {"status": "Pending"}, HTTPStatus.OK

    class ExecuteQuoteView(CicoView):
        summary = "Execute a given quote"
        parameters = [
            path_uuid_param("quote_id", "ID of an existing quote"),
            body_parameter(QuoteExecution),
        ]
        responses = {
            HTTPStatus.NO_CONTENT: response_definition(
                "Request accepted. You should poll for status updates."
            )
        }

        def post(self, quote_id: UUID):
            payment_method = (
                request.json["payment_method"]
                if "payment_method" in request.json
                else None
            )
            order_service.process_order(OrderId(quote_id), payment_method)
            return "OK", HTTPStatus.NO_CONTENT

    class GetRatesView(CicoView):
        summary = "Return rates for all Fiat and Diem currency pairs"
        responses = {
            HTTPStatus.OK: response_definition(
                "currency pairs with rates", schema=RateResponse
            ),
        }

        def get(self):
            rates = []
            for base_currency in DiemCurrency:
                for quote_currency in chain(
                    list(FiatCurrency.__members__), list(DiemCurrency.__members__)
                ):
                    if base_currency == quote_currency:
                        continue

                    one_diem = Amount().deserialize(Amount.unit)

                    conversion_rate = get_rate(
                        base_currency=Currency(base_currency),
                        quote_currency=Currency(quote_currency),
                    )
                    price = one_diem * conversion_rate

                    rates.append(
                        {
                            "currency_pair": f"{base_currency}_{quote_currency}",
                            "price": price.serialize(),
                        }
                    )

            return {"rates": rates}, HTTPStatus.OK
