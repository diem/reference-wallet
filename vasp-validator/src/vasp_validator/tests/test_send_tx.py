#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from ..vasp_proxy import VaspProxy, TxStatus

CURRENCY = "XUS"


def test_send_tx_travel_rule(vasp_proxy: VaspProxy, validator):
    """
    Successfully send a transaction requiring travel rule approval.
    """
    dest_address = validator.get_receiving_address()

    tx = vasp_proxy.send_transaction(dest_address, 1001, CURRENCY)

    assert tx.status == TxStatus.COMPLETED, (
        f"Failed to send transaction: {tx.status_description} \n"
        f"Validator state: {validator.get_offchain_state(tx.offchain_refid)}\n"
        f"VASP state: {vasp_proxy.get_offchain_state(tx.offchain_refid)} "
    )

    # VASP sent the transaction successfully. Validate that it was received by
    # the validator. If not, dump the Off-Chain state on both ends
    assert validator.knows_transaction(tx.onchain_version), (
        f"Transaction is not recognized by the validator \n"
        f"Validator state: {validator.get_offchain_state(tx.offchain_refid)} \n"
        f"VASP state: {vasp_proxy.get_offchain_state(tx.offchain_refid)} "
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
    # TBD: KYC abort codes are not defined yet in LRW
    assert (
        validator_offchain_state.payment.receiver.abort_code == "kyc_failure"
        and vasp_offchain_state.payment.receiver.abort_code == "kyc_failure"
    ), (
        f"Expected KYC failure \n"
        f"Validator state: {validator_offchain_state} \n"
        f"VASP state: {vasp_offchain_state} "
    )


def test_validator_in_manual_review(validator, vasp_proxy):
    """
    Send a transaction that requires manual KYC review by the receiver.
    """
    validator.kyc_manual_review()
    dest_address = validator.get_receiving_address()

    tx = vasp_proxy.send_transaction(dest_address, 1001, CURRENCY)

    assert tx.status == TxStatus.FAILED, (
        f"Transaction was sent although it should be pending KYC manual review \n"
        f"Validator state: {validator.get_offchain_state(tx.offchain_refid)}\n"
        f"VASP state: {vasp_proxy.get_offchain_state(tx.offchain_refid)} "
    )

    validator_offchain_state = validator.get_offchain_state(tx.offchain_refid)
    vasp_offchain_state = vasp_proxy.get_offchain_state(tx.offchain_refid)

    # VASP failed to send the transaction, but did it fail for the right reason?
    assert (
        validator_offchain_state.payment.receiver.status == "pending_review"
        and vasp_offchain_state.payment.receiver.status == "pending_review"
    ), (
        f"Expected KYC pending_review status \n"
        f"Validator state: {validator_offchain_state} \n"
        f"VASP state: {vasp_offchain_state} "
    )
