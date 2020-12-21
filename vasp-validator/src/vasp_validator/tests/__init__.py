#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import argparse
import pytest


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "vasp_proxy_module",
        help="Module path containing vasp_proxy_class",
    )
    parser.add_argument(
        "vasp_proxy_class",
        help="Instances of this class will be used to communicate with the tested VASP",
    )
    return parser.parse_args()


def automatic_validation_main():
    args = parse_args()
    pytest.main(
        [
            "--tb=short",
            "-p",
            "vasp_validator.tests.plugin",
            "--pyargs",
            "vasp_validator.tests.test_send_tx",
            "--vasp-proxy-module",
            args.vasp_proxy_module,
            "--vasp-proxy-class",
            args.vasp_proxy_class,
        ]
    )
