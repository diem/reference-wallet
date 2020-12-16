from tests.wallet_tests.services.system.utils import (
    add_incoming_transaction_to_blockchain,
    check_number_of_transactions,
)
from tests.wallet_tests.services.system.utils import (
    setup_inventory_with_initial_transaction,
)
from wallet.services.account import generate_sub_address
from wallet.services.system import sync_transaction
from wallet.storage import Transaction

OTHER_ADDRESS_1 = "257e50b131150fdb56aeab4ebe4ec2b9"
SUB_ADDRESS_1 = "8e298f642d08d1af"


def test_sync_transaction(patch_blockchain) -> None:
    setup_inventory_with_initial_transaction(
        patch_blockchain, 1000, mock_blockchain_initial_balance=1000
    )

    ADDED_VERSION = 2
    transaction = add_incoming_transaction_to_blockchain(
        patch_blockchain, generate_sub_address(), 100, OTHER_ADDRESS_1, 2, ADDED_VERSION
    )

    check_number_of_transactions(1)

    sync_transaction(transaction)

    check_number_of_transactions(2)

    assert (
        Transaction.query.filter_by(blockchain_version=ADDED_VERSION).first()
        is not None
    )
