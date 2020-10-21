import os
from http import HTTPStatus

from flask import Blueprint
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
            chain_id = os.getenv("CHAIN_ID")

            if chain_id == "1":
                return {"chain_id": 1, "display_name": "mainnet"}, HTTPStatus.OK
            if chain_id == "3":
                return {"chain_id": 3, "display_name": "devnet"}, HTTPStatus.OK
            if chain_id == "5":
                return {"chain_id": 5, "display_name": "premainnet"}, HTTPStatus.OK

            return {"chain_id": 2, "display_name": "testnet"}, HTTPStatus.OK
