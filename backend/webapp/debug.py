# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Union
from flask import (
    Blueprint,
    render_template,
)
from werkzeug.wrappers import Response
from wallet.storage import get_execution_logs


root = Blueprint("root", __name__, url_prefix="/")


@root.route("/execution_logs", methods=["GET"])
def list_execution_logs() -> Union[str, Response]:
    logs = get_execution_logs()
    return render_template("execution_logs.html", logs=logs)
