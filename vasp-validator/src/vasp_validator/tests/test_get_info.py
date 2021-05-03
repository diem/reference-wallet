import logging

from ..vasp_proxy import VaspProxy
import uuid
import time

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_get_info(validator, vasp_proxy: VaspProxy):
    validator_address = validator.get_receiving_address()
    reference_id = str(uuid.uuid4())

    # Step 1: vasp_proxy create payment command as sender
    vasp_proxy.create_payment_command_as_sender(
        reference_id=reference_id,
        vasp_address=validator_address,
    )

    payment_details = vasp_proxy.get_payment_info(reference_id, validator_address)

    assert payment_details is None

    assert vasp_proxy.knows_transaction_by_reference_id(
        reference_id
    ), f"Transaction {reference_id} is not recognized by the validator"
