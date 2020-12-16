from tests.wallet_tests.services.system.utils import (
    add_incoming_transaction_to_db,
    add_outgoing_transaction_to_db,
    setup_inventory_with_initial_transaction,
    check_balance,
    check_number_of_transactions,
    add_inventory_account_to_db,
    mock_account,
)
from wallet.services.system import sync_db

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
OTHER_ADDRESS_2 = "176b73399b04d9231769614cf22fb5df"
SUB_ADDRESS_2 = "a4d5bd88ec5be7a8"
SUB_ADDRESS_1 = "8e298f642d08d1af"


def test_sync_when_no_data_in_blockchain(patch_blockchain):
    """
    Setup:
        DB:
            1. inventory account with 1 incoming initial transaction of 1000 coins
            2. 1 user accounts with incoming transaction
            3. 1 user account with outgoing transaction
        Blockchain:
            EMPTY
    Action: sync_db() expected:
        2. Remove transactions from DB
    """
    add_inventory_account_to_db()
    mock_account(patch_blockchain, mocked_balance_value=45)

    add_incoming_transaction_to_db(
        receiver_sub_address=SUB_ADDRESS_1,
        amount=120,
        sender_address=OTHER_ADDRESS_1,
        sequence=1,
        version=1,
        account_name="test_account_1",
    )

    add_outgoing_transaction_to_db(
        sender_sub_address=SUB_ADDRESS_2,
        amount=35,
        receiver_address=OTHER_ADDRESS_2,
        sequence=1,
        version=5,
        account_name="test_account_2",
    )

    check_balance(85)
    check_number_of_transactions(2)
    sync_db()
    check_number_of_transactions(0)
    check_balance(0)
