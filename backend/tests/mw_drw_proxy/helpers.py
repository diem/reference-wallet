# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
import traceback
import random

import typing
from requests import HTTPError

DEFAULT_KYC_INFO = {
    "first_name": "Default",
    "last_name": "KYC",
    "dob": "1956-07-09",
    "phone": "1 202-456-1414",
    "address_1": "1840 Century Park East",
    "address_2": "",
    "city": "Los Angeles",
    "state": "California",
    "zip": "90067",
    "country": "US",
    "selected_fiat_currency": "USD",
    "selected_language": "en",
}


def convert_user_info_to_offchain(user_info: dict) -> dict:
    return {
        "payload_version": 1,
        "type": "individual",
        "given_name": user_info.get("first_name"),
        "surname": user_info.get("last_name"),
        "dob": user_info.get("dob"),
        "address": {
            "line1": user_info.get("address_1"),
            "line2": user_info.get("address_2"),
            "city": user_info.get("city"),
            "state": user_info.get("state"),
            "postal_code": user_info.get("zip"),
            "country": user_info.get("country"),
        },
    }


def convert_offchain_to_user_info(offchain: dict) -> dict:
    address = offchain.get("address") or {}
    return {
        **DEFAULT_KYC_INFO,
        "first_name": offchain.get("given_name"),
        "last_name": offchain.get("surname"),
        "dob": offchain.get("dob"),
        "address_1": address.get("line1"),
        "address_2": address.get("line2"),
        "city": address.get("city"),
        "state": address.get("state"),
        "zip": address.get("postal_code"),
        "country": address.get("country"),
        "selected_fiat_currency": "USD",
        "selected_language": "en",
    }


def error_response(logger: logging.Logger, e: Exception) -> typing.Tuple[dict, int]:
    # Use status code 418 (I'm a teapot) to indicate actual proxy server failures vs upstream issues
    status_code = 418
    if isinstance(e, HTTPError):
        status_code = e.response.status_code
        logger.warning(
            f"Got error: {e}. {e.request.method} - {e.request.path_url} - {e.request.body}"
        )
    else:
        backtrace = "\n".join(traceback.format_tb(e.__traceback__))
        logger.warning(f"Got error: {e}. \n{backtrace}")

    response = {
        "error": str(e),
        "stacktrace": traceback.format_tb(e.__traceback__),
    }
    return response, status_code
