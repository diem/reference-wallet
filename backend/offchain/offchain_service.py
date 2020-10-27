# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import asyncio
from threading import Thread
from offchainapi.core import Vasp


from . import vasp_info, offchain_business
from context import Context

import logging

logger = logging.getLogger(name="offchain-service")


def bootstrap(context: Context):
    vasp = make_vasp(context)
    launch(vasp)
    return vasp


def make_vasp(ctx: Context):
    return Vasp(
        ctx.config.vasp_libra_address(),
        host="0.0.0.0",
        port=ctx.config.offchain_service_port,
        business_context=offchain_business.LRW(ctx),
        info_context=vasp_info.LRW(ctx),
        database={},
    )


def start_thread(vasp, loop):
    # Initialize the VASP services.
    vasp.start_services()
    logger.info(f"thread start: {vasp}")

    try:
        # Start the loop
        loop.run_forever()
    finally:
        # Do clean up
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    logger.info("thread exit")


def launch(vasp):
    loop = asyncio.new_event_loop()
    vasp.set_loop(loop)

    # Create and launch a thread with the VASP event loop
    t = Thread(target=start_thread, args=(vasp, loop))
    t.start()

    # Block until the event loop in the thread is running.
    vasp.wait_for_start()
    logger.info("service started")
