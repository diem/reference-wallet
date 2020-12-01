# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from . import db_session
from .models import ExecutionLog


# logs to both database and stdout
def add_execution_log(message) -> None:
    # get the previous frame in the stack
    log = ExecutionLog(log=message, timestamp=datetime.utcnow())
    db_session.add(log)
    db_session.commit()


def get_execution_logs():
    return [log for log in ExecutionLog.query.all()]
