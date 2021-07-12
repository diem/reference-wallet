#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import pytest

from ..vasp_proxy import VaspProxy, TxStatus

CURRENCY = "XUS"


class TestTxSuccessWithTravelRule:
    def test_send(self, validator, vasp_proxy: VaspProxy):
        """
        The VASP successfully sends to the validator a transaction, requiring
        travel rule approval.
        """
        dest_address = validator.get_receiving_address()

        tx = vasp_proxy.send_transaction(dest_address, 2_000_000_000, CURRENCY)

        assert (
            tx.status == TxStatus.COMPLETED
        ), f"Failed to send transaction: {tx.status_description}"

        # VASP sent the transaction successfully. Validate that it was received
        # by the validator
        assert validator.knows_transaction_by_version(
            tx.onchain_version
        ), f"Transaction {tx.onchain_version} is not recognized by the validator"

    def test_receive(self, validator, vasp_proxy: VaspProxy):
        """
        The validator successfully sends to the VASP a transaction, requiring
        travel rule approval.
        """
        dest_address = vasp_proxy.get_receiving_address()

        tx = validator.send_transaction(dest_address, 2_000_000_000, CURRENCY)

        assert (
            tx.status == TxStatus.COMPLETED
        ), f"Failed to send transaction: {tx.status_description}"

        # Validator sent the transaction successfully. Validate that it was received
        # by the VASP
        assert vasp_proxy.knows_transaction_by_version(
            tx.onchain_version
        ), f"Transaction {tx.onchain_version} is not recognized by the VASP"


@pytest.mark.skip(
    reason="This test outlines future functionality. "
    "It is not runnable and will be skipped"
)
def test_validator_kyc_abort(validator, vasp_proxy):
    """
    Send a transaction that fails the KYC check on the receiving side.
    """
    validator.kyc_abort()
    dest_address = validator.get_receiving_address()

    # Currently `send_transaction` fails if the transaction is not sent
    # immediately. This is not necessarily the behavior that an actual
    # VASP would exhibit, but it is alright for now for this demonstration.
    tx = vasp_proxy.send_transaction(dest_address, 1001, CURRENCY)

    assert tx.status == TxStatus.FAILED, (
        f"This transaction should have failed \n"
        f"Validator state: {validator.get_offchain_state(tx.offchain_refid)}\n"
        f"VASP state: {vasp_proxy.get_offchain_state(tx.offchain_refid)} "
    )

    validator_offchain_state = validator.get_offchain_state(tx.offchain_refid)
    vasp_offchain_state = vasp_proxy.get_offchain_state(tx.offchain_refid)

    # VASP failed to send the transaction, but did it fail for the right reason?
    assert (
        validator_offchain_state.payment.receiver.abort_code == "kyc_failure"
        and vasp_offchain_state.payment.receiver.abort_code == "kyc_failure"
    ), (
        f"Expected KYC failure \n"
        f"Validator state: {validator_offchain_state} \n"
        f"VASP state: {vasp_offchain_state} "
    )
