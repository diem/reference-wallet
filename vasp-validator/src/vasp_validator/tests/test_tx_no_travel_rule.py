#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from ..vasp_proxy import VaspProxy, TxStatus

CURRENCY = "XUS"


def test_send_tx_no_travel_rule(validator, vasp_proxy: VaspProxy):
    """
    Successfully send a transaction not requiring travel rule approval.
    """
    dest_address = validator.get_receiving_address()

    tx = vasp_proxy.send_transaction(dest_address, 750, CURRENCY)

    assert (
        tx.status == TxStatus.COMPLETED
    ), f"Failed to send transaction: {tx.status_description}"

    # The amount is below $1000 so no off-chain interaction is required
    assert tx.offchain_refid is None

    # VASP sent the transaction successfully. Validate that it was received
    # by the validator
    assert validator.knows_transaction(
        tx.onchain_version
    ), f"Transaction {tx.onchain_version} is not recognized by the validator"


def test_receive_tx_no_travel_rule(validator, vasp_proxy: VaspProxy):
    """
    Successfully receive a transaction not requiring travel rule approval.
    """
    dest_address = vasp_proxy.get_receiving_address()

    tx = validator.send_transaction(dest_address, 750, CURRENCY)

    assert (
        tx.status == TxStatus.COMPLETED
    ), f"Failed to send transaction: {tx.status_description}"

    # The amount is below $1000 so no off-chain interaction is required
    assert tx.offchain_refid is None

    # VASP sent the transaction successfully. Validate that it was received
    # by the VASP
    assert vasp_proxy.knows_transaction(
        tx.onchain_version
    ), f"Transaction {tx.onchain_version} is not recognized by the VASP"


def test_send_tx_with_travel_rule(validator, vasp_proxy: VaspProxy):
    """
    Successfully send a transaction requiring travel rule approval.
    """
    dest_address = validator.get_receiving_address()

    tx = vasp_proxy.send_transaction(dest_address, 2_000_000_000, CURRENCY)

    assert (
        tx.status == TxStatus.COMPLETED
    ), f"Failed to send transaction: {tx.status_description}"

    # The amount is below $1000 so no off-chain interaction is required
    # assert tx.offchain_refid is None

    # VASP sent the transaction successfully. Validate that it was received
    # by the validator
    assert validator.knows_transaction(
        tx.onchain_version
    ), f"Transaction {tx.onchain_version} is not recognized by the validator"
