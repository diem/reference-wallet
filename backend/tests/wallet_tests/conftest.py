# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import context, pytest, typing


@pytest.fixture(autouse=True)
def env_context() -> typing.Generator[typing.Any, None, None]:
    context.set(context.from_env())
    yield
    context.set(None)
