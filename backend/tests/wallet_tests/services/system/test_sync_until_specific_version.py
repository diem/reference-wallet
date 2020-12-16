from tests.wallet_tests.services.system.utils import (
    check_balance,
    add_incoming_transaction_to_blockchain,
    add_outgoing_transaction_to_blockchain,
    check_number_of_transactions,
)
from tests.wallet_tests.services.system.utils import (
    setup_outgoing_transaction,
    setup_incoming_transaction,
    setup_inventory_with_initial_transaction,
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


def test_sync_until_specific_version(patch_blockchain):
    """
    Setup:
        DB:
            1. inventory account with 1 incoming initial transaction of 1000 coins
            2. 2 users accounts with outgoing transaction
            3. 1 user account with incoming transaction --> highest version - 10139
        Blockchain:
            1. 1 inventory incoming transaction
            2. 2 users incoming transactions --> 1 transaction with higher version from DB highest version (10151)
            3. 3 users outgoing transactions --> 1 transaction with lower version from DB highest version (10132)
    Action: sync_db() expected:
        1. Add transaction with version 4 into LRW DB
        2. Remove transaction with version 5 from LRW DB
    """
    setup_inventory_with_initial_transaction(
        patch_blockchain, 1000, mock_blockchain_initial_balance=880
    )

    NO_CHANGE_VERSION_1 = 10131
    setup_outgoing_transaction(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_1,
        amount=100,
        receiver_address=OTHER_ADDRESS_1,
        sequence=0,
        version=NO_CHANGE_VERSION_1,
        name="test_account",
    )

    NO_CHANGE_VERSION_2 = 10137
    setup_outgoing_transaction(
        patch_blockchain=patch_blockchain,
        sender_sub_address=SUB_ADDRESS_2,
        amount=75,
        receiver_address=OTHER_ADDRESS_2,
        sequence=1,
        version=NO_CHANGE_VERSION_2,
        name="test_account_2",
    )

    HIGHEST_VERSION_IN_DB = 10139
    setup_incoming_transaction(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=SUB_ADDRESS_3,
        amount=80,
        sender_address=OTHER_ADDRESS_3,
        sequence=12,
        version=HIGHEST_VERSION_IN_DB,
        name="test_account_3",
    )

    HIGHER_THAN_DB_HIHEST_VERSION = 10151
    add_incoming_transaction_to_blockchain(
        patch_blockchain,
        SUB_ADDRESS_4,
        25,
        OTHER_ADDRESS_4,
        7,
        HIGHER_THAN_DB_HIHEST_VERSION,
    )
    ADDED_VERSION = 10132
    add_outgoing_transaction_to_blockchain(
        patch_blockchain,
        SUB_ADDRESS_5,
        50,
        OTHER_ADDRESS_5,
        2,
        ADDED_VERSION,
    )

    check_balance(905)

    check_number_of_transactions(4)

    sync_db()

    check_number_of_transactions(5)

    check_balance(855)

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION_1).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=NO_CHANGE_VERSION_2).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=HIGHEST_VERSION_IN_DB).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(blockchain_version=ADDED_VERSION).first()
        is not None
    )

    assert (
        Transaction.query.filter_by(
            blockchain_version=HIGHER_THAN_DB_HIHEST_VERSION
        ).first()
        is None
    )
