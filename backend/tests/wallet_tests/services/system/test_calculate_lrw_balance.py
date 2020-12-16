from tests.wallet_tests.services.system.utils import (
    add_incoming_transaction_to_db,
    add_outgoing_transaction_to_db,
)
from wallet.services.system import calculate_lrw_balance


def test_calculate_lrw_balance(patch_blockchain):
    add_incoming_transaction_to_db(
        receiver_sub_address="3538b65dede30950",
        amount=2275,
        sender_address="D5AD1B71EFD4EE463BAF01FC7F281A8B",
        sequence=1,
        version=2,
        account_name="test_account",
    )

    add_outgoing_transaction_to_db(
        sender_sub_address="a4d5bd88ec5be7a8",
        amount=1800,
        receiver_address="257e50b131150fdb56aeab4ebe4ec2b9",
        sequence=1,
        version=4,
        account_name="test_account_2",
    )

    add_incoming_transaction_to_db(
        receiver_sub_address="93f3e11b980b9b13",
        amount=1160,
        sender_address="A95A3513300B2C8C1F530CF17D6819F7",
        sequence=1,
        version=8,
        account_name="test_account_3",
    )

    add_outgoing_transaction_to_db(
        sender_sub_address="5883abcebc7a5567",
        amount=920,
        receiver_address="176b73399b04d9231769614cf22fb5df",
        sequence=2,
        version=10,
        account_name="test_account_4",
    )

    lrw_balance = calculate_lrw_balance(6)

    assert lrw_balance == 475
