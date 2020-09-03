from threading import Thread
import time
import asyncio
import logging

from offchainapi.business import VASPInfo, BusinessContext, BusinessValidationFailure
from offchainapi.libra_address import LibraAddress
from offchainapi.payment_logic import PaymentCommand
from offchainapi.status_logic import Status
from offchainapi.payment import (
    PaymentAction,
    PaymentActor,
    PaymentObject,
    KYCData,
    StatusObject,
)
from offchainapi.crypto import ComplianceKey
from offchainapi.core import Vasp
from offchainapi.tests.basic_business_context import TestBusinessContext

logger = logging.getLogger(name="test_offchain")


PeerA_addr = LibraAddress.from_bytes(b"A" * 16)
PeerB_addr = LibraAddress.from_bytes(b"B" * 16)
peer_address = {
    PeerA_addr.as_str(): "http://localhost:8091",
    PeerB_addr.as_str(): "http://localhost:8092",
}

peer_keys = {
    PeerA_addr.as_str(): ComplianceKey.generate(),
    PeerB_addr.as_str(): ComplianceKey.generate(),
}


class SimpleVASPInfo(VASPInfo):
    def __init__(self, my_addr):
        self.my_addr = my_addr

    def get_peer_base_url(self, other_addr):
        assert other_addr.as_str() in peer_address
        return peer_address[other_addr.as_str()]

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
    print(f"Start Node {port}")

    # Block until the event loop in the thread is running.
    VASPx.wait_for_start()

    return (VASPx, loop, t)


async def test_main_perf(messages_num=10, wait_num=0, verbose=False):
    VASPa, loopA, tA = make_new_VASP(PeerA_addr, port=8091)
    VASPb, loopB, tB = make_new_VASP(PeerB_addr, port=8092, reliable=False)

    # Get the channel from A -> B
    channelAB = VASPa.vasp.get_channel(PeerB_addr)
    channelBA = VASPb.vasp.get_channel(PeerA_addr)

    # Define a payment command
    commands = []
    payments = []
    for cid in range(messages_num):
        peerA_addr = PeerA_addr.as_str()
        sub_a = LibraAddress.from_bytes(b"A" * 16, b"a" * 8).as_str()
        sub_b = LibraAddress.from_bytes(b"B" * 16, b"b" * 8).as_str()
        sender = PaymentActor(sub_a, StatusObject(Status.needs_kyc_data), [])
        receiver = PaymentActor(sub_b, StatusObject(Status.none), [])
        action = PaymentAction(10, "TIK", "charge", "2020-01-02 18:00:00 UTC")
        payment = PaymentObject(
            sender,
            receiver,
            f"{peerA_addr}_ref{cid:08d}",
            None,
            "Description ...",
            action,
        )
        kyc_data = asyncio.run_coroutine_threadsafe(
            VASPa.bc.get_extended_kyc(payment), loopA
        )
        kyc_data = kyc_data.result()
        payment.sender.add_kyc_data(kyc_data)
        payments += [payment]
        cmd = PaymentCommand(payment)
        commands += [cmd]

    async def send100(nodeA, commands):
        res = await asyncio.gather(
            *[nodeA.new_command_async(VASPb.my_addr, cmd) for cmd in commands],
            return_exceptions=True,
        )
        return res

    async def wait_for_all_payment_outcome(nodeA, payments, results):
        fut_list = [
            nodeA.wait_for_payment_outcome_async(p.reference_id)
            for p, r in zip(payments, results)
        ]

        res = await asyncio.gather(*fut_list, return_exceptions=True)

        return res

    # Execute 100 requests
    print("Inject commands")
    s = time.perf_counter()
    results = asyncio.run_coroutine_threadsafe(send100(VASPa, commands), loopA)
    results = results.result()

    # Print the result for all initial commands
    if verbose:  # verbose:
        for res in results:
            print("RES:", res)

    elapsed = time.perf_counter() - s

    print("Wait for all payments to have an outcome")
    outcomes = asyncio.run_coroutine_threadsafe(
        wait_for_all_payment_outcome(VASPa, payments, results), loopA
    )
    outcomes = outcomes.result()

    # Print the result for all requests
    if verbose:
        for out, res in zip(outcomes, results):
            if not isinstance(out, Exception):
                print("OUT OK:", out.sender.status, out.receiver.status)
            else:
                print("OUT NOTOK:", str(out))

    print("All payments done.")

    # Print some statistics
    success_number = sum([1 for r in results if type(r) == bool and r])
    print(f"Commands executed in {elapsed:0.2f} seconds.")
    print(f"Success #: {success_number}/{len(commands)}")

    assert success_number == len(commands)

    # In case you want to wait for other responses to settle
    #
    wait_for = wait_num
    for t in range(wait_for):
        print("waiting", t)
        await asyncio.sleep(1.0)

    # Check that all the payments have been processed and stored.
    for payment in payments:
        ref = payment.reference_id
        _ = VASPa.get_payment_by_ref(ref)
        hist = VASPa.get_payment_history_by_ref(ref)
        if verbose:
            if len(hist) > 1:
                print("--" * 40)
                for p in hist:
                    print(p.pretty())

    print(f"Estimate throughput #: {len(commands)/elapsed} Tx/s")

    # Close the loops
    VASPa.close()
    VASPb.close()

    # List the command obligations
    oblA = VASPa.pp.list_command_obligations()
    oblB = VASPb.pp.list_command_obligations()
    print(f"Pending processing: VASPa {len(oblA)} VASPb {len(oblB)}")

    # List the remaining retransmits
    rAB = channelAB.pending_retransmit_number()
    rBA = channelBA.pending_retransmit_number()
    print(f"Pending retransmit: VASPa {rAB} VASPb {rBA}")
