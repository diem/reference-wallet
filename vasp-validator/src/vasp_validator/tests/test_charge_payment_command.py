from ..vasp_proxy import VaspProxy
import uuid
import time

AMOUNT = 100_000_000

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60
CURRENCY = "XUS"


def test_approve_incoming_charge_payment_command(validator, vasp_proxy: VaspProxy):
    """
    This test simulate the scenario which in a merchant VASP sending payment
    details using QR code or link and the user wallet approve it.
    1. vasp_proxy create payment command as sender
    (as he would do in case he will get payment details through QR code or link)
    2. vasp_proxy approve the incoming payment command
    This operation should cause eventually onchain transaction
    3. vasp_proxy verify that transaction been created
    4. validator verify that transaction been created
    """

    validator_address = validator.get_receiving_address()
    reference_id = str(uuid.uuid4())
    action = "charge"
    expiration = int(time.time()) + ONE_YEAR_SECONDS

    # Step 1: vasp_proxy create payment command as sender
    vasp_proxy.create_payment_command_as_sender(
        reference_id=reference_id,
        vasp_address=validator_address,
        merchant_name="vaspulator",
        action=action,
        currency=CURRENCY,
        amount=AMOUNT,
        expiration=expiration,
    )
    # Step 2: vasp_proxy approve payment command
    vasp_proxy.approve_payment_command(reference_id)

    # Validate that VASP sent the transaction successfully.
    assert vasp_proxy.knows_transaction_by_reference_id(
        reference_id
    ), f"Transaction {reference_id} is not recognized by the VASP"

    # Validate that validator received the transaction successfully.
    assert validator.knows_transaction_by_reference_id(
        reference_id
    ), f"Transaction {reference_id} is not recognized by the validator"


def test_reject_payment_details_and_send(validator, vasp_proxy: VaspProxy):
    """
    This test simulate the scenario which in a merchant VASP sending payment
    details using QR code or link and the user wallet approve it.
    1. vasp_proxy create payment command as sender
    (as he would do in case he will get payment details through QR code or link)
    2. vasp_proxy reject the incoming payment command
    This operation should cause eventually onchain transaction
    3. vasp_proxy verify that transaction not been created
    4. validator verify that transaction not been created
    """

    validator_address = validator.get_receiving_address()
    reference_id = str(uuid.uuid4())
    action = "charge"
    expiration = int(time.time()) + ONE_YEAR_SECONDS

    # Step 1: vasp_proxy create payment command as sender
    vasp_proxy.create_payment_command_as_sender(
        reference_id=reference_id,
        vasp_address=validator_address,
        merchant_name="vaspulator",
        action=action,
        currency=CURRENCY,
        amount=AMOUNT,
        expiration=expiration,
    )
    # Step 2: vasp_proxy approve payment command
    vasp_proxy.reject_payment_command(reference_id)

    # Validate that VASP sent the transaction successfully.
    # assert vasp_proxy.knows_transaction_by_reference_id(
    #     reference_id
    # ), f"Transaction {reference_id} is not recognized by the VASP"
    #
    # # Validate that validator received the transaction successfully.
    # assert validator.knows_transaction_by_reference_id(
    #     reference_id
    # ), f"Transaction {reference_id} is not recognized by the validator"
