#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import os

from setuptools import setup

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="diem-vasp-validator",
    version="1.0.0",
    description="Diem VASP validation library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    url="https://github.com/diem/reference-wallet",
    package_dir={"": "src"},
    packages=["vasp_validator"],
    install_requires=[
        "diem>=1.1.0,<2.0.0",
        "dataclasses_json",
        "requests",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "validate-vasp = vasp_validator.tests:automatic_validation_main",
        ],
    },
    python_requires=">=3.7",
)
