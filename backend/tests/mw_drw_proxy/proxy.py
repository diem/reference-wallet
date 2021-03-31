# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import typing

from flask import Flask, request
import logging

from diem import identifier

from tests.e2e_tests import UserClient, create_test_user
from tests.mw_drw_proxy.helpers import (
    DEFAULT_KYC_INFO,
    convert_offchain_to_user_info,
    convert_user_info_to_offchain,
    error_response,
)

APP_NAME = __name__.split(".")[0]
LOG = logging.getLogger(APP_NAME)
logging.basicConfig(level=logging.INFO)

app: Flask = Flask(APP_NAME)

STATE: typing.Dict[str, UserClient] = {}

DRW_URL_PREFIX = os.getenv("DRW_URL_PREFIX", "https://demo-wallet.diem.com")


@app.route("/reset", methods=["GET", "POST"])
def reset_test():
    STATE.clear()


@app.route("/accounts", methods=["POST"])
def create_test_account():
    try:
        data = json.loads(request.data)

        # "{\"type\": \"individual\", \"payload_version\": 1, \"given_name\": \"Tom\", \"surname\": \"Jack\"}"
        if data.get("kyc_data") is None:
            kyc_info = DEFAULT_KYC_INFO
        else:
            # This may explode, and that's ok
            try:
                kyc_info = convert_offchain_to_user_info(json.loads(data["kyc_data"]))
            except Exception as e:
                LOG.error(f">>>> ERROR! {e}")
                raise

        uc = create_test_user(
            DRW_URL_PREFIX,
            f"{kyc_info['first_name']}_{kyc_info['last_name']}_{len(STATE)}".lower(),
            kyc_info=kyc_info,
            log_fn=LOG.info,
        )

        for currency, amount in (data["balances"] or {}).items():
            uc.buy(amount, currency, "USD")

        STATE[uc.name] = uc

        return {"id": uc.name, "kyc_data": data["kyc_data"]}

    except Exception as e:
        return error_response(LOG, e)


@app.route("/accounts/<account_id>/balances", methods=["GET"])
def account_balances(account_id):
    try:
        return {b["currency"]: b["balance"] for b in STATE[account_id].get_balances()}

    except Exception as e:
        return error_response(LOG, e)


@app.route("/accounts/<account_id>/payments", methods=["POST"])
def send_payment(account_id):
    try:
        # { "currency": "XUS", "amount": 0, "payee": "string" }
        data = json.loads(request.data)

        res = STATE[account_id].transfer(
            addr=data["payee"], amount=data["amount"], currency=data["currency"]
        )

        return {
            "id": res["id"],
            "account_id": account_id,
            "currency": res["currency"],
            "amount": res["amount"],
            "payee": data["payee"],
        }

    except Exception as e:
        return error_response(LOG, e)


@app.route("/accounts/<account_id>/payment_uris", methods=["POST"])
def get_payment_uri(account_id):
    try:
        address = STATE[account_id].get_recv_addr()

        return {
            "id": address,
            "account_id": account_id,
            "payment_uri": identifier.encode_intent(address, "", 0),
        }

    except Exception as e:
        return error_response(LOG, e)


@app.route("/kyc_sample", methods=["GET"])
def kyc_sample():
    return {
        "minimum": json.dumps(
            convert_user_info_to_offchain(
                {
                    **DEFAULT_KYC_INFO,
                    "first_name": "Accept",
                    "last_name": "KYC",
                }
            )
        ),
        "reject": json.dumps(
            convert_user_info_to_offchain(
                {
                    **DEFAULT_KYC_INFO,
                    "first_name": "Reject",
                    "last_name": "KYC",
                }
            )
        ),
        # TODO: these are not implemented yet
        "soft_match": json.dumps(
            convert_user_info_to_offchain(
                {
                    **DEFAULT_KYC_INFO,
                    "first_name": "SoftMatch",
                    "last_name": "KYC",
                }
            )
        ),
        "soft_reject": json.dumps(
            convert_user_info_to_offchain(
                {
                    **DEFAULT_KYC_INFO,
                    "first_name": "SoftReject",
                    "last_name": "KYC",
                }
            )
        ),
    }


if __name__ == "__main__":
    port = os.getenv("MW_DRW_PROXY_PORT", 3150)
    host = os.getenv("MW_DRW_PROXY_HOST", "localhost")
    LOG.info(
        f"Launching server on http://{host}:{port}  -  proxying to {DRW_URL_PREFIX}"
    )
    app.run(host=host, port=port)
