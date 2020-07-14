# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import UUID
from flask import Flask

from api import api
from errors import errors
from liquidity.liquidity import LiquidityProvider
from liquidity.storage import Session


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def _create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(errors)
    app.register_blueprint(api)
    app.json_encoder = UUIDEncoder
    app.debug = True
    return app


app: Flask = _create_app()


def init() -> Flask:
    print('starting init liquidity')
    with app.app_context():
        app.logger.info("init lp")
        LiquidityProvider.init_lp()
    return app


@app.teardown_appcontext
def remove_session(*args, **kwargs) -> None:  # pyre-ignore
    Session.remove()
