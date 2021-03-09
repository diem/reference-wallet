from tests.wallet_tests.services.system.utils import (
    check_balance,
    check_number_of_transactions,
    add_incoming_transaction_to_blockchain,
    add_outgoing_transaction_to_blockchain,
    mock_account,
    add_inventory_account_to_db,
    add_outgoing_transaction_to_db,
)
from wallet.services.system import sync_db

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
OTHER_ADDRESS_2 = "176b73399b04d9231769614cf22fb5df"
SUB_ADDRESS_2 = "a4d5bd88ec5be7a8"
SUB_ADDRESS_1 = "8e298f642d08d1af"


def test_sync_with_empty_db(patch_blockchain):
    """
    Setup:
        DB:
            1. inventory account with no transactions
        Blockchain:
            1. 1 inventory incoming transaction
            2. 1 user incoming transaction
            3. 1 user outgoing transaction
    Action: sync_db() expected:
        1. Add transactions to DB
    """
    add_inventory_account_to_db()
    mock_account(patch_blockchain, mocked_balance_value=45)

    add_outgoing_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_2,
        amount=75,
        receiver_address=OTHER_ADDRESS_2,
        sequence=1,
        version=0,
    )

    add_incoming_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_1,
        amount=120,
        sender_address=OTHER_ADDRESS_1,
        sequence=2,
        version=7,
    )

    check_balance(0)
    check_number_of_transactions(0)
    sync_db()
    check_number_of_transactions(2)
    check_balance(45)


def test_sync_with_db_with_orphan_tx(patch_blockchain):
    """
    Setup:
        DB:
            1. inventory account with no transactions
            2. there is one outgoing transaction that sill
               has no blockchain version and no sequence
        Blockchain:
            1. 1 inventory incoming transaction
            2. 1 user incoming transaction
            3. 1 user outgoing transaction
    Action: sync_db() expected:
        1. Add transactions to DB
    """
    add_inventory_account_to_db()
    mock_account(patch_blockchain, mocked_balance_value=45)

    add_outgoing_transaction_to_db(
        sender_sub_address=SUB_ADDRESS_2,
        amount=1,
        receiver_address=OTHER_ADDRESS_2,
        sequence=None,
        version=None,
        account_name="test_account_2",
    )

    add_outgoing_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_2,
        amount=75,
        receiver_address=OTHER_ADDRESS_2,
        sequence=1,
        version=0,
    )

    add_incoming_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_1,
        amount=120,
        sender_address=OTHER_ADDRESS_1,
        sequence=2,
        version=7,
    )

    check_balance(-1)
    check_number_of_transactions(1)
    sync_db()
    check_number_of_transactions(2)
    check_balance(45)
