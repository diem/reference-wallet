import os
from http import HTTPStatus

from flask import Blueprint
from diem import chain_ids
from webapp.schemas import Chain

from .strict_schema_view import StrictSchemaView, response_definition

system = Blueprint("system", __name__)


class SystemRoutes:
    class SystemView(StrictSchemaView):
        tags = ["System"]

    class GetNetworkView(SystemView):
        summary = "Get current chain"

        responses = {HTTPStatus.OK: response_definition("Current Chain", schema=Chain)}

        require_authenticated_user = False

        def get(self):
            chain_id = int(os.getenv("CHAIN_ID"))

            if chain_id == chain_ids.MAINNET.to_int():
                return (
                    {"chain_id": chain_ids.MAINNET.to_int(), "display_name": "mainnet"},
                    HTTPStatus.OK,
                )
            if chain_id == chain_ids.DEVNET.to_int():
                return (
                    {"chain_id": chain_ids.DEVNET.to_int(), "display_name": "devnet"},
                    HTTPStatus.OK,
                )
            if chain_id == chain_ids.PREMAINNET.to_int():
                return (
                    {
                        "chain_id": chain_ids.PREMAINNET.to_int(),
                        "display_name": "premainnet",
                    },
                    HTTPStatus.OK,
                )
            if chain_id == chain_ids.TESTNET.to_int():
                return (
                    {"chain_id": chain_ids.TESTNET.to_int(), "display_name": "testnet"},
                    HTTPStatus.OK,
                )
