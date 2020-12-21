#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from . import vasp_proxy_hook


def pytest_addoption(parser, pluginmanager):
    parser.addoption(
        "--vasp-proxy-module",
        dest="vasp_proxy_module",
        help="Module path containing vasp-proxy-class",
    )
    parser.addoption(
        "--vasp-proxy-class",
        dest="vasp_proxy_class",
        help="Instances of this class will be used to communicate with the tested VASP",
    )


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(vasp_proxy_hook)
