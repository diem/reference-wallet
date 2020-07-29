# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time
import uuid
from threading import Thread

from flasgger import Swagger
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from libra_utils.custody import Custody
from wallet import OnchainWallet
from wallet.config import ADMIN_USERNAME
from wallet.services.fx.fx import update_rates
from wallet.services.inventory import setup_inventory_account
from wallet.services.user import create_new_user
from wallet.storage import db_session
from wallet.storage.setup import setup_wallet_storage
from wallet.types import UsernameExistsError
from .debug import root
from .errors import errors
from .routes import admin, cico, user, account
from .swagger import swagger_template


def _init_admin_user():
    try:
        create_new_user(
            username=ADMIN_USERNAME,
            password=str(uuid.uuid4()),
            is_admin=True,
            first_name="Mrs.",
            last_name="Hudson",
        )
    except UsernameExistsError:
        pass


def _create_db(app: Flask) -> None:
    with app.app_context():
        setup_wallet_storage()
        app.logger.info("Database ready!")


def _init_onchain_wallet() -> None:
    Custody.init()
    OnchainWallet().setup_blockchain()


def _init_liquidity(app: Flask) -> None:
    with app.app_context():
        setup_inventory_account()


def _schedule_update_rates() -> None:
    def run():
        while True:
            update_rates()
            time.sleep(60)

    Thread(target=run, daemon=True).start()


def _create_app() -> Flask:
    app = Flask(__name__)

    # register api endpoints
    app.register_blueprint(user)
    app.register_blueprint(account)
    app.register_blueprint(errors)
    app.register_blueprint(root)
    app.register_blueprint(cico)
    app.register_blueprint(admin)

    # pyre-ignore[8]
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    Swagger(app, template=swagger_template)

    return app


app: Flask = _create_app()


def init() -> Flask:
    _create_db(app)
    _init_admin_user()
    _init_onchain_wallet()
    _init_liquidity(app)
    _schedule_update_rates()
    return app


@app.teardown_appcontext
def remove_session(*args, **kwargs) -> None:  # pyre-ignore
    db_session.remove()
