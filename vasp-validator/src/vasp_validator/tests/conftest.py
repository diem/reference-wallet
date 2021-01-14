#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import importlib
import logging
import os

import pytest
import requests

from diem import testnet, identifier

from ..validator_client import ValidatorClient
from ..vasp_proxy import VaspProxy

VALIDATOR_URL = os.environ["VALIDATOR_URL"]
CHAIN_ID = testnet.CHAIN_ID
HRP = identifier.HRPS[CHAIN_ID.to_int()]

log = logging.getLogger("vasp-proxy-plugin")


@pytest.fixture
def validator():
    return ValidatorClient.create(VALIDATOR_URL, " validator ")


@pytest.fixture
def vasp_proxy(pytestconfig) -> VaspProxy:
    vasp_proxy = pytestconfig.hook.pytest_create_vasp_proxy()
    vasp_proxy_module_path = pytestconfig.getoption("vasp_proxy_module", None)
    vasp_proxy_class_name = pytestconfig.getoption("vasp_proxy_class", None)

    if vasp_proxy and not vasp_proxy_module_path and not vasp_proxy_class_name:
        log.debug(f"Proxy object {vasp_proxy} created using hooks")
        return vasp_proxy

    if not vasp_proxy_module_path:
        raise ValueError(
            "VASP proxy module not specified. Use --vasp-proxy-module option or ensure "
            "the hook function pytest_create_vasp_proxy is registered before the tests"
        )

    if not vasp_proxy_class_name:
        raise ValueError(
            "VASP proxy module not specified. Use --vasp-proxy-class option or ensure "
            "the hook function pytest_create_vasp_proxy is registered before the tests"
        )

    vasp_proxy_module = importlib.import_module(vasp_proxy_module_path)
    vasp_proxy_class = getattr(vasp_proxy_module, vasp_proxy_class_name)
    vasp_proxy = vasp_proxy_class()
    log.debug(f"Proxy object {vasp_proxy} created using command line arguments")

    return vasp_proxy


@pytest.hookimpl(hookwrapper=True)
def pytest_exception_interact(node, call, report):
    """
    Intercept all HTTPError exceptions and improve how they are reported.
    """
    err = call.excinfo.value

    if report.when == "call" and isinstance(err, requests.exceptions.HTTPError):
        error_message = str(err)
        if err.response is not None:
            error_message += "\n" + err.response.text

        try:
            raise requests.exceptions.HTTPError(
                error_message, request=err.request, response=err.response
            ) from err
        except requests.exceptions.HTTPError as updated_err:
            call.excinfo._excinfo = (type(updated_err), updated_err)
            report.longrepr = node.repr_failure(call.excinfo)

    yield
