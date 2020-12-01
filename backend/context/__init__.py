# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing
from .context import from_config, from_env, for_local_dev, generate, Context


# a global variable for storing shared instance, use get / set to access
_context: typing.Optional[Context] = None


def set(ctx: typing.Optional[Context]) -> None:
    global _context
    _context = ctx


def get() -> Context:
    global _context
    if _context is None:
        raise ValueError("global context is not initialized")
    return typing.cast(Context, _context)
