from ..vasp_proxy import VaspProxy
import uuid
import time

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_get_info(validator, vasp_proxy: VaspProxy):
    """
    This test simulate the scenario which in a merchant VASP sending minimal payment
    details (only reference_id and vasp_address) using QR code or link and the user wallet approve it.
    1. vasp_proxy create payment command as sender
    (as he would do in case he will get payment details through QR code or link)
    2. vasp_proxy approve the incoming payment command
    This operation should cause eventually onchain transaction
    3. vasp_proxy verify that transaction been created
    4. validator verify that transaction been created
    """

    validator_address = validator.get_receiving_address()
    reference_id = str(uuid.uuid4())

    # Step 1: vasp_proxy create payment command as sender
    vasp_proxy.create_payment_command_as_sender(
        reference_id=reference_id,
        vasp_address=validator_address,
    )

    payment_details = vasp_proxy.get_payment_details(reference_id)

    assert payment_details is None
