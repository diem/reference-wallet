from tests.wallet_tests.services.system.utils import (
    add_incoming_transaction_to_db,
    setup_inventory_with_initial_transaction,
    setup_incoming_transaction,
    setup_outgoing_transaction,
)
from tests.wallet_tests.services.system.utils import (
    check_balance,
    add_outgoing_transaction_to_blockchain,
    check_number_of_transactions,
)
from wallet.services.system import sync_db
from wallet.storage import Transaction

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
OTHER_ADDRESS_2 = "176b73399b04d9231769614cf22fb5df"
OTHER_ADDRESS_3 = "0498D148D9A4DCCF893A480B32FF08DA"
OTHER_ADDRESS_4 = "A95A3513300B2C8C1F530CF17D6819F7"
OTHER_ADDRESS_5 = "D5AD1B71EFD4EE463BAF01FC7F281A8B"
SUB_ADDRESS_1 = "8e298f642d08d1af"
SUB_ADDRESS_2 = "a4d5bd88ec5be7a8"
SUB_ADDRESS_3 = "3b3b97168de2f9de"
SUB_ADDRESS_4 = "c59a28326b9caa2a"
SUB_ADDRESS_5 = "6e17b494e79dab75"


def test_sync_multiple_transactions(patch_blockchain):
    """
    Setup:
        DB:
            1. inventory account with 1 incoming initial transaction of 1000 coins
            2. 3 users accounts with incoming transaction
            3. 1 user account with outgoing transaction
        Blockchain:
            1. 1 inventory incoming transaction
            2. 2 users incoming transactions
            3. 2 users outgoing transactions
    Action: sync_db() expected:
        1. Add transaction with version 4 into LRW DB
        2. Remove transaction with version 5 from LRW DB
    """
    setup_inventory_with_initial_transaction(
        patch_blockchain, 1000, mock_blockchain_initial_balance=1000
    )

    NO_CHANGE_VERSION_1 = 1
    setup_incoming_transaction(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_1,
        amount=100,
        sender_address=OTHER_ADDRESS_1,
        sequence=1,
        version=NO_CHANGE_VERSION_1,
        name="test_account",
    )

    NO_CHANGE_VERSION_2 = 2
    setup_outgoing_transaction(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_2,
        amount=75,
        receiver_address=OTHER_ADDRESS_2,
        sequence=2,
        version=NO_CHANGE_VERSION_2,
        name="test_account_2",
    )

    NO_CHANGE_VERSION_3 = 3
    setup_incoming_transaction(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_3,
        amount=50,
        sender_address=OTHER_ADDRESS_3,
        sequence=3,
        version=NO_CHANGE_VERSION_3,
        name="test_account_3",
    )

    # should be removed during sync
    REMOVED_VERSION = 5
    add_incoming_transaction_to_db(
        receiver_sub_address=SUB_ADDRESS_4,
        amount=25,
        sender_address=OTHER_ADDRESS_4,
        sequence=5,
        version=REMOVED_VERSION,
        account_name="test_account_4",
    )

    # should be added during sync
    ADDED_VERSION = 4
    add_outgoing_transaction_to_blockchain(
        patch_blockchain, SUB_ADDRESS_5, 200, OTHER_ADDRESS_5, 4, ADDED_VERSION
    )

    check_balance(1100)

    check_number_of_transactions(5)

    sync_db()

    check_number_of_transactions(5)

    check_balance(875)

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION_1).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION_2).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION_3).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=ADDED_VERSION).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=REMOVED_VERSION).first() is None
    )
