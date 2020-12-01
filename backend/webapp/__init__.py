# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict
import logging

import context
import time
import uuid
from threading import Thread
from flasgger import Swagger
from flask import Flask
from offchain import offchain_service, client as offchain_client
from wallet.services.system import sync_db
from werkzeug.middleware.proxy_fix import ProxyFix

from wallet.config import ADMIN_USERNAME
from wallet.services.fx.fx import update_rates
from wallet.services.inventory import setup_inventory_account
from wallet.services.user import create_new_user
from wallet.storage import db_session
from wallet.storage.setup import setup_wallet_storage
from wallet.types import UsernameExistsError
from .debug import root
from .errors import errors
from .routes import admin, cico, user, account, system
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


def _schedule_update_rates() -> None:
    def run():
        while True:
            update_rates()
            time.sleep(60)

    Thread(target=run, daemon=True).start()


def _sync_db() -> None:
    def run():
        while True:
            try:
                sync_db()
            except Exception:
                logging.getLogger("sync-db").exception("sync db failed")

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
    app.register_blueprint(system)

    # pyre-ignore[8]
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    Swagger(app, template=swagger_template)

    return app


app: Flask = _create_app()


def _init_context():
    context.set(context.from_env())


def _init_offchain():
    vasp = offchain_service.make_vasp(context.get())
    offchain_service.launch(vasp)
    offchain_client.set(vasp)


def init():
    with app.app_context():
        _init_with_log("context", _init_context)
        _init_with_log("storage", setup_wallet_storage)
        _init_with_log("admin_user", _init_admin_user)
        _init_with_log("offchain", _init_offchain)
        _init_with_log("liquidity", setup_inventory_account)
        _init_with_log("update_rates_thread", _schedule_update_rates)
        _init_with_log("sync-db", _sync_db)
    return app


@app.teardown_appcontext
def remove_session(*args, **kwargs) -> None:  # pyre-ignore
    db_session.remove()


def _init_with_log(title, fn):
    app.logger.info(f"Start init {title}")
    fn()
    app.logger.info(f"{title} is initialized")
