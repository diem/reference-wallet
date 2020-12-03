# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Union, Tuple
from uuid import UUID

from flask import Blueprint, Response, jsonify, request, current_app

from diem_utils.types.liquidity.currency import Currency, CurrencyPair
from diem_utils.types.liquidity.errors import AlreadySettled
from diem_utils.types.liquidity.quote import QuoteId
from diem_utils.types.liquidity.settlement import DebtId
from diem_utils.types.liquidity.trade import Direction, TradeId

from liquidity.liquidity import LiquidityProvider

api = Blueprint("api/v1", __name__, url_prefix="/")


def json_response(json):
    return current_app.response_class(
        response=json, status=HTTPStatus.OK, mimetype="application/json"
    )


@api.route("/details", methods=["GET"])
def lp_details() -> Union[str, Response]:
    current_app.logger.info(f"/details start")
    lp = LiquidityProvider()
    json = lp.lp_details().to_json()
    current_app.logger.info(f"/details response: {json}")
    return json_response(json)


@api.route("/quote", methods=["POST"])
def get_quote() -> Union[str, Response]:
    lp = LiquidityProvider()
    data = request.get_json()

    current_app.logger.info(f"request for quote {data}")
    base_currency = Currency[data["base_currency"]]
    quote_currency = Currency[data["quote_currency"]]
    pair = CurrencyPair(base=base_currency, quote=quote_currency)
    quote = lp.get_quote(pair=pair, amount=int(data["amount"]))
    json = quote.to_json()
    current_app.logger.info(f"quote {json}")
    return json_response(json)


@api.route("/trade", methods=["POST"])
def trade_and_execute() -> Union[str, Response]:
    lp = LiquidityProvider()
    data = request.get_json()
    quote_id = QuoteId(UUID(data["quote_id"]))
    direction = Direction[data["direction"]]
    diem_deposit_address = (
        data["diem_deposit_address"] if "diem_deposit_address" in data else None
    )
    tx_version = int(data["tx_version"]) if "tx_version" in data else None

    trade_id = lp.trade_and_execute(
        quote_id=quote_id,
        direction=direction,
        diem_bech32_deposit_address=diem_deposit_address,
        tx_version=tx_version,
    )
    return jsonify({"trade_id": str(trade_id)})


@api.route("/trade/<uuid:trade_id_param>", methods=["GET"])
def trade_info(trade_id_param: UUID) -> Union[str, Response]:
    lp = LiquidityProvider()
    trade_id = TradeId(trade_id_param)
    trade_data = lp.trade_info(trade_id=trade_id)
    json = trade_data.to_json()
    current_app.logger.info(f"Trade info {json}")
    return json_response(json)


@api.route("/debt", methods=["GET"])
def get_debt() -> Union[str, Response]:
    lp = LiquidityProvider()
    debts = lp.get_debt()
    serializable_debts = [debt.to_dict() for debt in debts]

    current_app.logger.info(f"Debt info {serializable_debts}")
    return jsonify({"debts": serializable_debts})


@api.route("/debt/<uuid:debt_id_param>", methods=["PUT"])
def settle(debt_id_param: UUID) -> Union[str, Response, Tuple[str, int]]:
    settlement_confirmation = request.get_json()["settlement_confirmation"]

    lp = LiquidityProvider()
    try:
        lp.settle(DebtId(debt_id_param), settlement_confirmation)
    except KeyError as e:
        return str(e), 404
    except AlreadySettled as e:
        return str(e), 409

    return "OK"
