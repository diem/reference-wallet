from tests.wallet_tests.services.system.utils import (
    add_user_in_db,
    add_incoming_user_transaction_to_db,
    add_outgoing_user_transaction_to_db,
)
from wallet.storage import Transaction
from wallet.storage import (
    get_account_transactions,
    DiemCurrency,
)

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


def test_get_account_transactions():
    user = add_user_in_db("user_test")

    add_incoming_user_transaction_to_db(
        amount=100,
        receiver_sub_address=SUB_ADDRESS_1,
        sender_address=OTHER_ADDRESS_1,
        sequence=0,
        user=user,
        version=1,
        account_name="user_test",
    )
    add_outgoing_user_transaction_to_db(
        amount=75,
        account_name="user_test",
        receiver_address=OTHER_ADDRESS_2,
        sender_sub_address=SUB_ADDRESS_2,
        sequence=1,
        user=user,
        version=2,
    )
    add_incoming_user_transaction_to_db(
        amount=50,
        receiver_sub_address=SUB_ADDRESS_3,
        sender_address=OTHER_ADDRESS_3,
        sequence=2,
        user=user,
        version=2,
        account_name="user_test",
    )
    add_incoming_user_transaction_to_db(
        amount=25,
        receiver_sub_address=SUB_ADDRESS_4,
        sender_address=OTHER_ADDRESS_4,
        sequence=3,
        user=user,
        version=4,
        account_name="user_test",
    )
    add_outgoing_user_transaction_to_db(
        amount=75,
        account_name="user_test",
        receiver_address=OTHER_ADDRESS_5,
        sender_sub_address=SUB_ADDRESS_5,
        sequence=1,
        user=user,
        version=5,
    )

    transactions = Transaction.query.all()

    print(transactions)

    transactions = get_account_transactions(
        account_id=user.account.id, currency=DiemCurrency.Coin1
    )

    assert len(transactions) == 5


def test_get_account_transactions_tp_to_version():
    user = add_user_in_db("user_test")

    add_incoming_user_transaction_to_db(
        amount=100,
        receiver_sub_address=SUB_ADDRESS_1,
        sender_address=OTHER_ADDRESS_1,
        sequence=0,
        user=user,
        version=1,
        account_name="user_test",
    )
    add_outgoing_user_transaction_to_db(
        amount=75,
        account_name="user_test",
        receiver_address=OTHER_ADDRESS_2,
        sender_sub_address=SUB_ADDRESS_2,
        sequence=1,
        user=user,
        version=2,
    )
    add_incoming_user_transaction_to_db(
        amount=50,
        receiver_sub_address=SUB_ADDRESS_3,
        sender_address=OTHER_ADDRESS_3,
        sequence=2,
        user=user,
        version=2,
        account_name="user_test",
    )
    add_incoming_user_transaction_to_db(
        amount=25,
        receiver_sub_address=SUB_ADDRESS_4,
        sender_address=OTHER_ADDRESS_4,
        sequence=3,
        user=user,
        version=4,
        account_name="user_test",
    )
    add_outgoing_user_transaction_to_db(
        amount=75,
        account_name="user_test",
        receiver_address=OTHER_ADDRESS_5,
        sender_sub_address=SUB_ADDRESS_5,
        sequence=1,
        user=user,
        version=5,
    )

    transactions = get_account_transactions(
        account_id=user.account.id, currency=DiemCurrency.Coin1, up_to_version=3
    )

    assert len(transactions) == 3
