# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

from offchain import make_new_VASP, LRW_VASP_ADDR
from threading import Thread
import asyncio

DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")


def start_thread_main(vasp, loop):
    # Initialize the VASP services.
    vasp.start_services()
    print("Started thread main", flush=True)

    try:
        # Start the loop
        loop.run_forever()
    finally:
        # Do clean up
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    print("VASP loop exit...", flush=True)


def init_vasp(vasp):
    loop = asyncio.new_event_loop()
    vasp.set_loop(loop)

    # Create and launch a thread with the VASP event loop
    t = Thread(target=start_thread_main, args=(vasp, loop))
    t.start()
    print(f"Start Node {vasp.port}", flush=True)

    # Block until the event loop in the thread is running.
    vasp.wait_for_start()

    print(f"Node {vasp.port} started", flush=True)
    return vasp, loop, t


VASP, loop, thread = init_vasp(make_new_VASP(LRW_VASP_ADDR))
print(f"VASP {VASP} started", flush=True)
