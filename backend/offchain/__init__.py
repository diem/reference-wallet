# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from threading import Thread
import asyncio
from offchainapi.core import Vasp
from offchainapi.business import VASPInfo
from offchainapi.libra_address import LibraAddress
from offchainapi.crypto import ComplianceKey
from wallet.onchainwallet import OnchainWallet

# from .offchain_business import LRWOffChainBusinessContext
from offchainapi.tests.basic_business_context import TestBusinessContext


LRW_VASP_ADDR = LibraAddress.from_bytes(bytes.fromhex(OnchainWallet().vasp_address))
LRW_VASP_COMPLIANCE_KEY = ComplianceKey.from_str(os.getenv("VASP_COMPLIANCE_KEY"))

PeerB_addr = LibraAddress.from_bytes(b"B" * 16)
peer_address = {
    LRW_VASP_ADDR.as_str(): "http://localhost:8091",
    PeerB_addr.as_str(): "http://localhost:8092",
}
peer_b_key = ComplianceKey.generate()
peer_keys = {
    LRW_VASP_ADDR.as_str(): LRW_VASP_COMPLIANCE_KEY,
    PeerB_addr.as_str(): peer_b_key,
}


class SimpleVASPInfo(VASPInfo):
    def __init__(self, my_addr):
        self.my_addr = my_addr

    def get_peer_base_url(self, other_addr):
        other_vasp_addr = other_addr.get_onchain_encoded_str()
        assert other_vasp_addr in peer_address
        return peer_address[other_vasp_addr]

    def get_peer_compliance_verification_key(self, other_addr):
        key = ComplianceKey.from_str(peer_keys[other_addr].export_pub())
        assert not key._key.has_private
        return key

    def get_peer_compliance_signature_key(self, my_addr):
        return peer_keys[my_addr]

    def is_authorised_VASP(self, certificate, other_addr):
        return True


def start_thread_main(vasp, loop):
    # Initialize the VASP services.
    vasp.start_services()

    try:
        # Start the loop
        loop.run_forever()
    finally:
        # Do clean up
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    print("VASP loop exit...")


def make_new_VASP(Peer_addr, port, reliable=True):
    VASPx = Vasp(
        Peer_addr,
        host="localhost",
        port=port,
        business_context=TestBusinessContext(Peer_addr, reliable=reliable),
        info_context=SimpleVASPInfo(Peer_addr),
        database={},
    )

    loop = asyncio.new_event_loop()
    VASPx.set_loop(loop)

    # Create and launch a thread with the VASP event loop
    t = Thread(target=start_thread_main, args=(VASPx, loop))
    t.start()
    print(f"Start Node {port}", flush=True)

    # Block until the event loop in the thread is running.
    VASPx.wait_for_start()

    print(f"Node {port} started", flush=True)

    return (VASPx, loop, t)


def init_vasp():
    VASP, loop, t = make_new_VASP(LRW_VASP_ADDR, port=8091)


DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")
VASP, loop, thread = make_new_VASP(LRW_VASP_ADDR, port=8091)
print(f"VASP {VASP} started", flush=True)
