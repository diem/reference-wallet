import logging
import os

from diem import jsonrpc, diem_types
from sqlalchemy import desc
from sqlalchemy_paginator import Paginator
from wallet.services import account as account_service, INVENTORY_ACCOUNT_NAME
from wallet.services.account import generate_new_subaddress
from wallet.storage import (
    get_transaction_by_blockchain_version,
    add_transaction,
    TransactionStatus,
    TransactionType,
    delete_transaction_by_id,
    Account,
    Transaction,
    SubAddress,
)

CURRENCY = "Coin1"
PAGE_SIZE = 10

VASP_ADDRESS = os.getenv("VASP_ADDR")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")

logger = logging.getLogger("sync-db")


def sync_db():
    client = jsonrpc.Client(JSON_RPC_URL)
    onchain_account = client.get_account(VASP_ADDRESS)

    up_to_version = (
        Transaction.query.filter_by(type=TransactionType.EXTERNAL)
        .order_by(desc(Transaction.blockchain_version))
        .first()
        .blockchain_version
    )

    if sync_required(onchain_account, up_to_version):
        sync(client, onchain_account, up_to_version)
    else:
        logger.info("balances equal, no synchronization required")


def sync_required(onchain_account, up_to_version):
    onchain_balance = get_onchain_balance(onchain_account)
    db_balance = calculate_lrw_balance(up_to_version)

    return onchain_balance != db_balance


def get_onchain_balance(account):
    for balance in account.balances:
        if balance.currency == CURRENCY:
            return balance.amount
    else:
        raise Exception(f"Failed find balance for currency {CURRENCY}")


def calculate_lrw_balance(up_to_version):
    db_balance = 0
    query = Account.query
    paginator = Paginator(query, PAGE_SIZE)

    for page in paginator:
        accounts = page.object_list

        for account in accounts:
            balance = account_service.get_account_balance_by_id(
                account_id=account.id, up_to_version=up_to_version,
            ).total.get(CURRENCY)

            logger.info(f"account name {account.name} balance {balance}")
            db_balance += balance

    return db_balance


def sync(client, onchain_account, up_to_version):
    # sync incoming transaction
    incoming_processed_transactions = sync_transactions(
        onchain_account.received_events_key, client, up_to_version
    )
    # sync outgoing transaction
    outgoing_processed_transactions = sync_transactions(
        onchain_account.sent_events_key, client, up_to_version
    )
    processed_transactions = incoming_processed_transactions.union(
        outgoing_processed_transactions
    )
    remove_redundant(processed_transactions)


def sync_transactions(events_key, client, up_to_version):
    start = 0
    processed_transactions = set()

    while True:
        events = client.get_events(
            event_stream_key=events_key, start=start, limit=PAGE_SIZE
        )

        if not events:
            return processed_transactions

        for event in events:
            blockchain_version = event.transaction_version

            transaction = client.get_transactions(blockchain_version, 1)[0]

            if transaction.version <= up_to_version:
                sync_transaction(transaction)

            processed_transactions.add(transaction.version)

        start += PAGE_SIZE


def sync_transaction(transaction):
    if transaction.transaction.script.type == "peer_to_peer_with_metadata":
        blockchain_version = transaction.version

        transaction_from_db = get_transaction_by_blockchain_version(blockchain_version)

        if transaction_from_db is None:
            add_transaction_to_db(transaction)
        else:
            logger.info(f"Transaction version {blockchain_version} was found in DB")


def add_transaction_to_db(transaction):
    metadata = transaction.transaction.script.metadata

    receiver_sub_address = None
    sender_sub_address = None

    if metadata:
        receiver_sub_address, sender_sub_address = deserialize_metadata(metadata)

    source_id = None
    destination_id = None

    sender_address = transaction.transaction.sender
    receiver_address = transaction.transaction.script.receiver

    # outgoing transaction
    if sender_address.lower() == VASP_ADDRESS.lower():
        sender_sub_address, source_id = handle_outgoing_transaction(sender_sub_address)
    # incoming transaction
    elif receiver_address.lower() == VASP_ADDRESS.lower():
        destination_id, receiver_sub_address = handle_incoming_transaction(
            receiver_sub_address
        )
    else:
        logger.warning(
            f"LRW VASP address is not the source nor the destination of transaction with version {transaction.version}"
        )

        return None

    add_transaction(
        amount=transaction.transaction.script.amount,
        currency=transaction.transaction.script.currency,
        payment_type=TransactionType.EXTERNAL,
        status=TransactionStatus.COMPLETED,
        source_id=source_id,
        source_address=sender_address,
        source_subaddress=sender_sub_address,
        destination_id=destination_id,
        destination_address=receiver_address,
        destination_subaddress=receiver_sub_address,
        sequence=transaction.transaction.sequence_number,
        blockchain_version=transaction.version,
    )


def deserialize_metadata(metadata):
    metadata = diem_types.Metadata.lcs_deserialize(bytes.fromhex(metadata)).value.value

    receiver_sub_address = None
    sender_sub_address = None

    if metadata.to_subaddress:
        receiver_sub_address = metadata.to_subaddress.hex()

    if metadata.from_subaddress:
        sender_sub_address = metadata.from_subaddress.hex()

    return receiver_sub_address, sender_sub_address


def remove_redundant(processed_transactions):
    query = Transaction.query
    paginator = Paginator(query, PAGE_SIZE)

    for page in paginator:
        transactions = page.object_list

        for transaction in transactions:
            if (
                transaction.type == TransactionType.EXTERNAL
                and transaction.blockchain_version not in processed_transactions
            ):
                logger.info(
                    f"transaction with blockchain version {transaction.blockchain_version} was not found in "
                    f"blockchain while synchronization and therefore is been deleted "
                )

                delete_transaction_by_id(transaction.id)


def handle_outgoing_transaction(sender_sub_address):
    if sender_sub_address:
        sender_sub_record = SubAddress.query.filter_by(
            address=sender_sub_address
        ).first()

        if sender_sub_record:
            source_id = sender_sub_record.account_id
        else:
            source_id = Account.query.filter_by(name=INVENTORY_ACCOUNT_NAME).first().id
    else:
        source_id = Account.query.filter_by(name=INVENTORY_ACCOUNT_NAME).first().id
        sender_sub_address = generate_new_subaddress(source_id)

    return sender_sub_address, source_id


def handle_incoming_transaction(receiver_sub_address):
    if receiver_sub_address:
        sub_address_record = SubAddress.query.filter_by(
            address=receiver_sub_address
        ).first()

        if sub_address_record:
            destination_id = sub_address_record.account_id
        else:
            destination_id = (
                Account.query.filter_by(name=INVENTORY_ACCOUNT_NAME).first().id
            )
    else:
        destination_id = Account.query.filter_by(name=INVENTORY_ACCOUNT_NAME).first().id
        receiver_sub_address = generate_new_subaddress(destination_id)

    return destination_id, receiver_sub_address
