#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import os

from vasp_validator.vasp_proxy import VaspProxy
from .vasp_proxy_testee import VaspProxyTestee

TESTEE_URL = os.environ["TESTEE_URL"]


def pytest_create_vasp_proxy() -> VaspProxy:
    """
    This is a hook function used by vasp_validator plugin.
    If defined, it will be called to created instances of the VASP proxy object.
    """
    return VaspProxyTestee(TESTEE_URL)
