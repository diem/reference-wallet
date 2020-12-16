from tests.wallet_tests.services.system.utils import (
    check_balance,
    check_number_of_transactions,
)
from tests.wallet_tests.services.system.utils import (
    add_outgoing_transaction_to_db,
    setup_inventory_with_initial_transaction,
    setup_outgoing_transaction,
)
from wallet.services.system import sync_db
from wallet.storage import Transaction

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
OTHER_ADDRESS_2 = "176b73399b04d9231769614cf22fb5df"
SUB_ADDRESS_2 = "a4d5bd88ec5be7a8"
SUB_ADDRESS_1 = "8e298f642d08d1af"


def test_remove_outgoing_transaction_from_db(patch_blockchain) -> None:
    """
    Setup:
        DB:
            1. inventory account with 1 incoming initial transaction of 1000 coins
            2. 2 user accounts with outgoing transaction
        Blockchain:
            1. 1 inventory incoming transaction
            2. 1 user outgoing transaction
    Action: sync_db() expected:
        1. Remove transaction with version 1 from LRW DB
    """
    setup_inventory_with_initial_transaction(
        patch_blockchain=patch_blockchain,
        initial_funds=1000,
        mock_blockchain_initial_balance=1100,
    )

    REMOVED_VERSION = 1
    add_outgoing_transaction_to_db(
        sender_sub_address=SUB_ADDRESS_1,
        amount=100,
        receiver_address=OTHER_ADDRESS_1,
        sequence=1,
        version=REMOVED_VERSION,
        account_name="test_account",
    )

    NO_CHANGE_VERSION = 2
    setup_outgoing_transaction(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_2,
        amount=75,
        receiver_address=OTHER_ADDRESS_2,
        sequence=2,
        version=NO_CHANGE_VERSION,
        name="test_account_2",
    )

    check_balance(825)

    check_number_of_transactions(3)

    sync_db()

    check_number_of_transactions(2)

    check_balance(925)

    assert (
        Transaction.query.filter_by(blockchain_version=REMOVED_VERSION).first() is None
    )

    assert Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION) is not None
