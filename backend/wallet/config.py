# pyre-strict

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context
import os
import sys
from typing import Optional

import logging

logging.basicConfig(
    format="[%(asctime)s][%(threadName)s][%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)


DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin@lrw")
ADMIN_LOGIN_ENABLED: bool = (
    True if os.getenv("ADMIN_LOGIN_ENABLED") is not None else False
)

SECRET_KEY: str = os.getenv("SECRET_KEY", "you-will-never-guess")

if "VASP_ADDR" in os.environ:
    context.set(context.from_env())
