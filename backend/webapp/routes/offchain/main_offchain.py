# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging

from offchain import (
    X_REQUEST_ID,
    X_REQUEST_SENDER_ADDRESS,
)
from flask import Blueprint, request
from flask.views import MethodView
from wallet.services.offchain import (
    offchain as offchain_service,
)
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
)

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


class OffchainMainRoute:
    class OffchainView(StrictSchemaView):
        tags = ["Offchain"]

    class OffchainV2View(MethodView):
        def dispatch_request(self, *args, **kwargs):
            x_request_id = request.headers.get(X_REQUEST_ID)
            sender_address = request.headers.get(X_REQUEST_SENDER_ADDRESS)
            request_body = request.get_data()

            logger.info(f"[{sender_address}:{x_request_id}] offchain v2 income request")

            code, response = offchain_service.process_inbound_command(
                sender_address, request_body
            )

            logger.info(
                f"[{sender_address}:{x_request_id}] response: {code}, {response}"
            )

            return (response, code, {X_REQUEST_ID: x_request_id})
