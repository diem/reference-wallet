from ..vasp_proxy import VaspProxy
import uuid
import time

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60
CURRENCY = "XUS"


def test_approve_incoming_charge_payment_command(validator, vasp_proxy: VaspProxy):
    """
    This test simulate the scenario which in a merchant VASP sending payment
    details using QR code or link and the user wallet approve it.
    1. validator create payment command as receiver
    (as he would do before generate a QR code or link)
    2. vasp_proxy create payment command as sender
    (as he would do in case he will get payment details through QR code or link)
    3. vasp_proxy approve the incoming payment command
    This operation should cause eventually onchain transaction
    4. vasp_proxy verify that transaction been created
    5. validator verify that transaction been created
    """

    reference_id = str(uuid.uuid4())
    vasp_proxy_address = vasp_proxy.get_receiving_address()
    print(f"~~~~~~ vasp_proxy_address (sender): {vasp_proxy_address}")
    action = "charge"
    amount = 2_000_000_000
    expiration = int(time.time()) + ONE_YEAR_SECONDS
    # Step 1: validator create payment command as receiver
    validator_address = validator.create_payment_command_as_receiver(
        reference_id=reference_id,
        # sender_address=vasp_proxy_address,
        action=action,
        currency=CURRENCY,
        amount=amount,
        expiration=expiration,
    )
    # Step 2: vasp_proxy create payment command as sender
    print(f"~~~~~~ validator_address (receiver): {validator_address}")
    vasp_proxy.create_payment_command_as_sender(
        reference_id=reference_id,
        vasp_address=validator_address,
        merchant_name="vaspulator",
        action=action,
        currency=CURRENCY,
        amount=amount,
        expiration=expiration,
    )
    # Step 3: vasp_proxy approve payment command
    vasp_proxy.approve_payment_command(reference_id)

    # VASP sent the transaction successfully. Validate that it was received
    # by the validator
    assert validator.knows_transaction_by_reference_id(
        reference_id
    ), f"Transaction {reference_id} is not recognized by the validator"


def test_reject_payment_details_and_send(validator, vasp_proxy: VaspProxy):
    ...
