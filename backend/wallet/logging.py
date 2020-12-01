# pyre-strict

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from functools import wraps
import typing
import logging, inspect

from wallet.storage.logs import add_execution_log

RT = typing.TypeVar("RT")
TFun = typing.Callable[..., typing.Optional[RT]]


def log_execution(message: str) -> None:
    frame = inspect.currentframe()
    if not frame:
        return
    # pyre-ignore
    func = frame.f_back.f_code
    log_str = "%s: %s in %s:%i" % (
        message,
        func.co_name,
        func.co_filename,
        func.co_firstlineno,
    )
    logging.debug(log_str)
    add_execution_log(log_str)


def debug_log(
    logger: typing.Optional[typing.Callable[[str], None]] = None,
) -> typing.Callable[[TFun], TFun]:
    """
    Print function details on function crash
    Args:
        logger: Logger to use. If None, print.
    """

    def deco_log(f: TFun) -> TFun:
        @wraps(f)
        def log_function(*args, **kwargs):  # pyre-ignore
            try:
                msg = "Executing function: {}, args: {}, kwargs: {}".format(
                    f.__name__, args, kwargs
                )
                if logger:
                    logger(msg)
                else:
                    print(msg)
                return f(*args, **kwargs)
            except Exception as e:
                msg = "FAILED to execute function: {}, args: {}, kwargs: {}, error: {}".format(
                    f.__name__, args, kwargs, e
                )
            if logger:
                logger(msg)
            else:
                print(msg)
            return f(*args, **kwargs)

        return typing.cast(TFun, log_function)  # true decorator

    return deco_log
