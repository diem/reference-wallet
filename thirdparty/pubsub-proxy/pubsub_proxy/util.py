#!/usr/bin/env python3
import importlib
from typing import Any


def load_custom_backend(path: str) -> Any:
    parts = path.split(".")
    module = importlib.import_module(".".join(parts[:-1]))
    return getattr(module, parts[-1])


def transform_address(address: bytes) -> str:
    # TODO: deprecate this function after pylibra upgrade
    return address.hex()[-32:]
