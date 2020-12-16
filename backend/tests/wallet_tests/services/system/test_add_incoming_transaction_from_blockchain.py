from tests.wallet_tests.services.system.utils import (
    check_balance,
    add_incoming_transaction_to_blockchain,
    check_number_of_transactions,
)
from tests.wallet_tests.services.system.utils import (
    setup_inventory_with_initial_transaction,
    setup_incoming_transaction,
)
from wallet.services.system import sync_db
from wallet.storage import Transaction

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
OTHER_ADDRESS_2 = "176b73399b04d9231769614cf22fb5df"
SUB_ADDRESS_2 = "a4d5bd88ec5be7a8"
SUB_ADDRESS_1 = "8e298f642d08d1af"


def test_add_incoming_transaction_from_blockchain(patch_blockchain) -> None:
    """
    Setup:
        DB:
            1. inventory account with 1 incoming initial transaction of 1000 coins
            2. 1 user account with incoming transaction
        Blockchain:
            1. 1 inventory incoming transaction
            2. 2 user incoming transactions
    Action: sync_db() expected:
        1. Add transaction with version 2 into LRW DB
    """
    setup_inventory_with_initial_transaction(
        patch_blockchain, 1000, mock_blockchain_initial_balance=1175
    )

    NO_CHANGE_VERSION = 6
    setup_incoming_transaction(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_1,
        amount=100,
        sender_address=OTHER_ADDRESS_1,
        sequence=6,
        version=NO_CHANGE_VERSION,
        name="test_account",
    )

    # should be added during sync
    ADDED_VERSION = 2
    add_incoming_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_2,
        amount=75,
        sender_address=OTHER_ADDRESS_2,
        sequence=2,
        version=ADDED_VERSION,
    )

    check_balance(1100)

    check_number_of_transactions(2)

    sync_db()

    check_number_of_transactions(3)

    check_balance(1175)

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=ADDED_VERSION).first()
        is not None
    )
