from datetime import datetime

from diem.txnmetadata import general_metadata
from sqlalchemy_paginator import Paginator
from tests.wallet_tests.client_sdk_mocks import (
    MockEventData,
    MockEventResource,
    MockedBalance,
    MockTransactionP2PScript,
    MockTransactionDetails,
    MockSignedTransaction,
)
from wallet.services import INVENTORY_ACCOUNT_NAME
from wallet.services.system import VASP_ADDRESS
from wallet.storage import (
    db_session,
    Transaction,
    SubAddress,
    User,
    RegistrationStatus,
    FiatCurrency,
    Account,
    TransactionType,
    TransactionStatus,
)
from wallet.services import account as account_service

DD_ADDRESS = "000000000000000000000000000000DD"
CURRENCY = "Coin1"
RECEIVED_EVENTS_KEY = "020000000000000095f6ce2c353b3fb1f6a7636f38883ddd"
SENT_EVENTS_KEY = "030000000000000095f6ce2c353b3fb1f6a7636f38883ddd"


def add_inventory_account_with_initial_funds_to_blockchain(
    patch_blockchain, amount, mocked_initial_balance
):
    mock_account(patch_blockchain, mocked_balance_value=mocked_initial_balance)

    tx = mock_transaction(
        metadata=None,
        amount=amount,
        receiver_address=VASP_ADDRESS,
        sequence_number=0,
        sender_address=DD_ADDRESS,
        version=0,
    )

    txs = [tx]
    patch_blockchain.add_account_transactions(addr_hex=VASP_ADDRESS, txs=txs)

    event = mock_event(
        amount=amount,
        receiver_address=VASP_ADDRESS,
        sender_address=DD_ADDRESS,
        events_key=RECEIVED_EVENTS_KEY,
        sequence_number=0,
        version=0,
    )

    events = [event]

    patch_blockchain.add_events(RECEIVED_EVENTS_KEY, events)


def mock_account(patch_blockchain, mocked_balance_value):
    account = patch_blockchain.get_account_resource(address_hex=VASP_ADDRESS)
    balance = MockedBalance()
    balance.currency = CURRENCY
    balance.amount = mocked_balance_value
    account.balances = [balance]
    account.set_received_events_key(RECEIVED_EVENTS_KEY)
    account.set_sent_events_key(SENT_EVENTS_KEY)


def add_inventory_account_with_initial_funds_to_db(amount):
    inventory_user = User(
        username=INVENTORY_ACCOUNT_NAME,
        registration_status=RegistrationStatus.Approved,
        selected_fiat_currency=FiatCurrency.USD,
        selected_language="en",
        password_salt="123",
        password_hash="deadbeef",
    )

    inventory_user.account = Account(name=INVENTORY_ACCOUNT_NAME)

    tx = Transaction(
        created_timestamp=datetime.now(),
        amount=amount,
        currency=CURRENCY,
        type=TransactionType.EXTERNAL,
        status=TransactionStatus.COMPLETED,
        sequence=0,
        blockchain_version=0,
        source_address=DD_ADDRESS,
        destination_address=VASP_ADDRESS,
        destination_id=inventory_user.id,
    )

    inventory_user.account.received_transactions.append(tx)

    db_session.add(inventory_user)
    db_session.commit()


def setup_incoming_transaction(
    patch_blockchain,
    receiver_sub_address,
    amount,
    sender_address,
    sequence,
    version,
    name,
):
    add_incoming_transaction_to_db(
        receiver_sub_address=receiver_sub_address,
        amount=amount,
        sender_address=sender_address,
        sequence=sequence,
        version=version,
        account_name=name,
    )

    add_incoming_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        receiver_sub_address=receiver_sub_address,
        amount=amount,
        sender_address=sender_address,
        sequence=sequence,
        version=version,
    )


def add_incoming_transaction_to_db(
    receiver_sub_address, amount, sender_address, sequence, version, account_name,
):
    user = add_user_in_db(account_name=account_name)

    add_incoming_user_transaction_to_db(
        amount=amount,
        receiver_sub_address=receiver_sub_address,
        sender_address=sender_address,
        sequence=sequence,
        user=user,
        version=version,
        account_name=account_name,
    )


def add_user_in_db(account_name):
    user = User(
        username=account_name,
        registration_status=RegistrationStatus.Approved,
        selected_fiat_currency=FiatCurrency.USD,
        selected_language="en",
        password_salt="123",
        password_hash="deadbeef",
    )

    user.account = Account(name=account_name)
    db_session.add(user)
    db_session.commit()

    return user


def add_incoming_user_transaction_to_db(
    amount, receiver_sub_address, sender_address, sequence, user, version, account_name
):
    tx = Transaction(
        source_address=sender_address,
        destination_address=VASP_ADDRESS,
        amount=amount,
        sequence=sequence,
        blockchain_version=version,
    )
    tx.created_timestamp = datetime.now()
    tx.type = TransactionType.EXTERNAL
    tx.currency = CURRENCY
    tx.status = TransactionStatus.COMPLETED
    tx.destination_id = user.id
    tx.destination_subaddress = receiver_sub_address
    user.account.received_transactions.append(tx)

    user_account_id = Account.query.filter_by(name=account_name).first().id

    db_session.add(SubAddress(address=receiver_sub_address, account_id=user_account_id))

    db_session.commit()


def setup_inventory_with_initial_transaction(
    patch_blockchain, initial_funds, mocked_initial_balance
):
    add_inventory_account_with_initial_funds_to_db(amount=initial_funds)
    add_inventory_account_with_initial_funds_to_blockchain(
        patch_blockchain=patch_blockchain,
        amount=initial_funds,
        mocked_initial_balance=mocked_initial_balance,
    )


def add_outgoing_transaction_to_db(
    sender_sub_address, amount, receiver_address, sequence, version, account_name
):
    user = add_user_in_db(account_name)

    add_outgoing_user_transaction_to_db(
        amount=amount,
        account_name=account_name,
        receiver_address=receiver_address,
        sender_sub_address=sender_sub_address,
        sequence=sequence,
        user=user,
        version=version,
    )


def add_outgoing_user_transaction_to_db(
    amount, account_name, receiver_address, sender_sub_address, sequence, user, version
):
    user_account_id = Account.query.filter_by(name=account_name).first().id
    tx = Transaction(
        amount=amount,
        sequence=sequence,
        blockchain_version=version,
        source_address=VASP_ADDRESS,
        destination_address=receiver_address,
    )

    tx.created_timestamp = datetime.now()
    tx.type = TransactionType.EXTERNAL
    tx.currency = CURRENCY
    tx.status = TransactionStatus.COMPLETED
    tx.source_id = user.id
    tx.source_subaddress = sender_sub_address
    user.account.sent_transactions.append(tx)

    db_session.add(SubAddress(address=sender_sub_address, account_id=user_account_id))

    db_session.commit()


def setup_outgoing_transaction(
    patch_blockchain,
    sender_sub_address,
    amount,
    receiver_address,
    sequence,
    version,
    name,
):
    add_outgoing_transaction_to_db(
        sender_sub_address=sender_sub_address,
        amount=amount,
        receiver_address=receiver_address,
        sequence=sequence,
        version=version,
        account_name=name,
    )
    add_outgoing_transaction_to_blockchain(
        patch_blockchain=patch_blockchain,
        sender_sub_address=sender_sub_address,
        amount=amount,
        receiver_address=receiver_address,
        sequence=sequence,
        version=version,
    )


def check_balance(expected_balance):
    lrw_balance = 0
    query = Account.query
    paginator = Paginator(query, 20)

    for page in paginator:
        accounts = page.object_list

        for account in accounts:
            balance = account_service.get_account_balance(
                account=account, up_to_version=0,
            ).total.get(CURRENCY)

            lrw_balance += balance

    assert lrw_balance == expected_balance


def check_number_of_transactions(expected):
    assert Transaction.query.count() == expected


def add_incoming_transaction_to_blockchain(
    patch_blockchain, receiver_sub_address, amount, sender_address, sequence, version,
):
    metadata_1 = general_metadata(to_subaddress=bytes.fromhex(receiver_sub_address))
    transaction = mock_transaction(
        metadata=metadata_1.hex(),
        amount=amount,
        receiver_address=VASP_ADDRESS,
        sequence_number=sequence,
        sender_address=sender_address,
        version=version,
    )
    event = mock_event(
        metadata=metadata_1.hex(),
        amount=amount,
        receiver_address=VASP_ADDRESS,
        sender_address=sender_address,
        events_key=RECEIVED_EVENTS_KEY,
        sequence_number=sequence,
        version=version,
    )

    patch_blockchain.add_account_transactions(addr_hex=VASP_ADDRESS, txs=[transaction])

    patch_blockchain.add_events(RECEIVED_EVENTS_KEY, [event])

    return transaction


def add_outgoing_transaction_to_blockchain(
    patch_blockchain, sender_sub_address, amount, receiver_address, sequence, version,
):
    metadata = general_metadata(from_subaddress=bytes.fromhex(sender_sub_address))
    transaction = mock_transaction(
        metadata=metadata.hex(),
        amount=amount,
        receiver_address=receiver_address,
        sequence_number=sequence,
        sender_address=VASP_ADDRESS,
        version=version,
    )

    event = mock_event(
        metadata=metadata.hex(),
        amount=amount,
        receiver_address=receiver_address,
        sender_address=VASP_ADDRESS,
        events_key=SENT_EVENTS_KEY,
        sequence_number=sequence,
        version=version,
    )

    patch_blockchain.add_account_transactions(addr_hex=VASP_ADDRESS, txs=[transaction])

    patch_blockchain.add_events(SENT_EVENTS_KEY, [event])


def mock_transaction(
    metadata, amount, receiver_address, sequence_number, sender_address, version
):
    script = MockTransactionP2PScript(
        amount=amount, receiver=receiver_address, metadata=metadata
    )

    transaction = MockTransactionDetails(
        sequence_number=sequence_number, sender=sender_address, script=script
    )

    return MockSignedTransaction(transaction=transaction, version=version)


def mock_event(
    amount,
    receiver_address,
    sender_address,
    events_key,
    sequence_number,
    version,
    metadata: str = None,
):
    event_data_1 = MockEventData(
        amount=amount,
        metadate=metadata,
        receiver=receiver_address,
        sender=sender_address,
    )

    return MockEventResource(
        data=event_data_1,
        key=events_key,
        sequence_number=sequence_number,
        transaction_version=version,
    )
