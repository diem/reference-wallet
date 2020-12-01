# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from diem import diem_types
from diem_utils.types.currencies import DiemCurrency
from wallet.services import account as account_service
from wallet.services.risk import risk_check
from . import INVENTORY_ACCOUNT_NAME
from .log import add_transaction_log
from .. import storage, services
from ..logging import log_execution
from time import time
from ..storage import (
    add_transaction,
    Transaction,
    get_transaction_by_details,
    get_total_currency_credits,
    get_total_currency_debits,
    get_reference_id_from_transaction_id,
    get_transaction_status,
    get_transaction_id_from_reference_id,
    get_metadata_signature_from_reference_id,
)
from ..storage import get_account_id_from_subaddr, get_account
from ..types import (
    TransactionDirection,
    TransactionType,
    TransactionStatus,
    BalanceError,
    Balance,
)
from offchainapi.libra_address import LibraAddress
from offchainapi.payment import PaymentAction, PaymentActor, PaymentObject, StatusObject
from offchainapi.payment_logic import PaymentCommand
from offchainapi.status_logic import Status
from offchain import client as offchain_client, get_new_offchain_reference_id

import context, logging

logger = logging.getLogger(name="wallet-service:transaction")


class RiskCheckError(Exception):
    pass


class SelfAsDestinationError(Exception):
    pass


class InvalidTravelRuleMetadata(Exception):
    pass


def decode_general_metadata_v0(
    metadata_bytes: bytes,
) -> Optional[diem_types.GeneralMetadataV0]:
    metadata = diem_types.Metadata.lcs_deserialize(metadata_bytes)

    if isinstance(metadata, diem_types.Metadata__GeneralMetadata):
        if isinstance(
            metadata.value, diem_types.GeneralMetadata__GeneralMetadataVersion0
        ):
            return metadata.value.value
    raise None


def process_incoming_transaction(
    blockchain_version: int,
    sender_address: str,
    receiver_address: str,
    sequence: int,
    amount: int,
    currency: DiemCurrency,
    metadata: diem_types.Metadata,
):
    logger.info(
        f"process_incoming_transaction: sender: {sender_address}, receiver: {receiver_address}, seq: {sequence}, amount: {amount}"
    )
    log_execution("Attempting to process incoming transaction from chain")
    receiver_id = None
    sender_subaddress = None
    receiver_subaddr = None

    if isinstance(metadata, diem_types.Metadata__GeneralMetadata) and isinstance(
        metadata.value, diem_types.GeneralMetadata__GeneralMetadataVersion0
    ):
        general_v0 = metadata.value.value

        if general_v0.to_subaddress:
            receiver_subaddr = general_v0.to_subaddress.hex()
            receiver_id = get_account_id_from_subaddr(receiver_subaddr)

        if general_v0.from_subaddress:
            sender_subaddress = general_v0.from_subaddress.hex()

    if isinstance(metadata, diem_types.Metadata__TravelRuleMetadata) and isinstance(
        metadata.value, diem_types.TravelRuleMetadata__TravelRuleMetadataVersion0
    ):
        travel_rule_v0 = metadata.value.value
        reference_id = travel_rule_v0.off_chain_reference_id

        if reference_id is None:
            raise InvalidTravelRuleMetadata(
                f"Invalid Travel Rule metadata : reference_id None"
            )

        transaction_id = get_transaction_id_from_reference_id(reference_id)
        transaction = get_transaction(transaction_id)

        if (
            transaction.amount == amount
            and transaction.status == TransactionStatus.READY_FOR_ON_CHAIN
            and transaction.source_address == sender_address
            and transaction.destination_address == receiver_address
        ):
            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.COMPLETED,
                sequence=sequence,
                blockchain_tx_version=blockchain_version,
            )

            return

        raise InvalidTravelRuleMetadata(
            f"Travel Rule metadata decode failed: Transaction {transaction_id} with reference ID {reference_id} "
            f"should have amount: {transaction.amount}, status: {TransactionStatus.READY_FOR_ON_CHAIN}, "
            f"source address: {transaction.source_address}, destination address: {transaction.destination_address},"
            f" but received transaction has amount: {amount}, status: {transaction.status}, "
            f"source address: {sender_address}, destination address: {receiver_address}"
        )

    if not receiver_id:
        log_execution("Incoming transaction had no metadata. crediting inventory")
        receiver_id = get_account(account_name=INVENTORY_ACCOUNT_NAME).id

    if get_transaction_by_details(
        source_address=sender_address,
        source_subaddress=sender_subaddress,
        sequence=sequence,
    ):
        log_execution(
            f"Incoming transaction sequence {sequence} already exists. Aborting"
        )
        return

    tx = add_transaction(
        amount=amount,
        currency=currency,
        payment_type=TransactionType.EXTERNAL,
        status=TransactionStatus.COMPLETED,
        source_address=sender_address,
        source_subaddress=sender_subaddress,
        destination_id=receiver_id,
        destination_address=receiver_address,
        destination_subaddress=receiver_subaddr,
        sequence=sequence,
        blockchain_version=blockchain_version,
    )

    logger.info(
        f"process_incoming_transaction: Successfully saved transaction from on-chain, receiver_id: {receiver_id}"
    )
    log_str = "Settled On Chain"
    add_transaction_log(tx.id, log_str)
    log_execution(f"Processed incoming transaction, saving internally as txn {tx.id}")


def send_transaction(
    sender_id: int,
    amount: int,
    currency: DiemCurrency,
    destination_address: str,
    destination_subaddress: Optional[str] = None,
    payment_type: Optional[TransactionType] = None,
) -> Optional[Transaction]:
    log_execution(
        f"transfer from sender {sender_id} to receiver ({destination_subaddress} {destination_address})"
    )

    if account_service.is_own_address(
        sender_id=sender_id,
        receiver_vasp=destination_address,
        receiver_subaddress=destination_subaddress,
    ):
        raise SelfAsDestinationError(
            "It is not possible to send transaction to your own wallet."
        )

    if not risk_check(sender_id, amount):
        return _send_transaction_external_offchain(
            sender_id=sender_id,
            destination_address=destination_address,
            destination_subaddress=destination_subaddress,
            amount=amount,
            currency=currency,
        )

    if destination_subaddress is None:
        return _unhosted_wallet_transfer(
            sender_id=sender_id, destination_address=destination_address
        )

    if account_service.is_in_wallet(destination_subaddress, destination_address):
        return _send_transaction_internal(
            sender_id=sender_id,
            destination_subaddress=destination_subaddress,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
        )
    else:
        return _send_transaction_external(
            sender_id=sender_id,
            destination_address=destination_address,
            destination_subaddress=destination_subaddress,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
        )


def _unhosted_wallet_transfer(sender_id, destination_address):
    # TODO handle unhosted wallet transfer
    log_execution(
        f"transfer to unhosted wallet transfer from {sender_id} to receiver {destination_address}"
    )
    return None


def _send_transaction_external(
    sender_id,
    destination_address,
    destination_subaddress,
    payment_type,
    amount,
    currency,
) -> Optional[Transaction]:
    log_execution(
        f"external transfer from {sender_id} to receiver {destination_address}, "
        f"receiver subaddress {destination_subaddress}"
    )
    payment_type = TransactionType.EXTERNAL if payment_type is None else payment_type
    return external_transaction(
        sender_id=sender_id,
        receiver_address=destination_address,
        receiver_subaddress=destination_subaddress,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
    )


def _send_transaction_internal(
    sender_id, destination_subaddress, payment_type, amount, currency
) -> Optional[Transaction]:
    log_execution(
        f"internal transfer from {sender_id} to receiver {destination_subaddress}"
    )
    receiver_id = get_account_id_from_subaddr(subaddr=destination_subaddress)
    payment_type = TransactionType.INTERNAL if payment_type is None else payment_type

    return internal_transaction(
        sender_id=sender_id,
        receiver_id=receiver_id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
    )


def _send_transaction_external_offchain(
    sender_id, destination_address, destination_subaddress, amount, currency,
) -> Optional[Transaction]:
    log_execution(
        f"Offchain external transaction from {sender_id} to receiver {destination_address}, "
        f"receiver subaddress {destination_subaddress}"
    )
    return external_offchain_transaction(
        sender_id=sender_id,
        receiver_address=destination_address,
        receiver_subaddress=destination_subaddress,
        amount=amount,
        currency=currency,
        payment_type=TransactionType.OFFCHAIN,
    )


def update_transaction(
    transaction_id: int,
    status: Optional[TransactionStatus] = None,
    sequence: Optional[int] = None,
    blockchain_tx_version: Optional[int] = None,
) -> None:
    storage.update_transaction(
        transaction_id=transaction_id,
        sequence=sequence,
        status=status,
        blockchain_version=blockchain_tx_version,
    )


def get_transaction(
    transaction_id: Optional[int] = None, blockchain_version: Optional[int] = None
) -> Transaction:
    if transaction_id:
        return storage.get_transaction(transaction_id)
    if blockchain_version:
        return storage.get_transaction_by_blockchain_version(blockchain_version)


def get_transaction_direction(
    account_id: int, transaction: Transaction
) -> TransactionDirection:
    if transaction.destination_id == account_id:
        return TransactionDirection.RECEIVED

    if transaction.source_id == account_id:
        return TransactionDirection.SENT

    raise LookupError("Couldn't determine transaction direction")


def validate_balance(sender_id: int, amount: int, currency: DiemCurrency) -> bool:
    account_balance = account_service.get_account_balance_by_id(account_id=sender_id)
    return amount <= account_balance.total[currency]


def internal_transaction(
    sender_id: int,
    receiver_id: int,
    amount: int,
    currency: DiemCurrency,
    payment_type: TransactionType,
) -> Transaction:
    """Transfer transaction between accounts in the LRW internal ledger."""

    log_execution("Enter internal_transaction")

    if not validate_balance(sender_id, amount, currency):
        raise BalanceError(
            f"Balance {account_service.get_account_balance_by_id(account_id=sender_id).total[currency]} "
            f"is less than amount needed {amount}"
        )

    sender_subaddress = account_service.generate_new_subaddress(sender_id)
    receiver_subaddress = account_service.generate_new_subaddress(receiver_id)
    internal_vasp_address = context.get().config.vasp_address

    transaction = add_transaction(
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        status=TransactionStatus.COMPLETED,
        source_id=sender_id,
        source_address=internal_vasp_address,
        source_subaddress=sender_subaddress,
        destination_id=receiver_id,
        destination_address=internal_vasp_address,
        destination_subaddress=receiver_subaddress,
    )

    log_execution(
        f"Transfer from {sender_id} to {receiver_id} started with transaction id {transaction.id}"
    )
    add_transaction_log(transaction.id, "Transfer completed")
    return transaction


def external_transaction(
    sender_id: int,
    receiver_address: str,
    receiver_subaddress: str,
    amount: int,
    currency: DiemCurrency,
    payment_type: TransactionType,
) -> Transaction:
    logger.info(
        f"external_transaction {sender_id} to receiver {receiver_address}, "
        f"receiver subaddress {receiver_subaddress}, amount {amount}"
    )
    if not validate_balance(sender_id, amount, currency):
        raise BalanceError(
            f"Balance {account_service.get_account_balance_by_id(account_id=sender_id).total[currency]} "
            f"is less than amount needed {amount}"
        )

    sender_onchain_address = context.get().config.vasp_address
    sender_subaddress = account_service.generate_new_subaddress(account_id=sender_id)

    transaction = add_transaction(
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        status=TransactionStatus.PENDING,
        source_id=sender_id,
        source_address=sender_onchain_address,
        source_subaddress=sender_subaddress,
        destination_id=None,
        destination_address=receiver_address,
        destination_subaddress=receiver_subaddress,
    )

    if services.run_bg_tasks():
        from ..background_tasks.background import async_external_transaction

        async_external_transaction.send(transaction.id)
    else:
        submit_onchain(transaction_id=transaction.id)

    return transaction


def external_offchain_transaction(
    sender_id: int,
    receiver_address: str,
    receiver_subaddress: str,
    amount: int,
    currency: DiemCurrency,
    payment_type: TransactionType,
    original_payment_reference_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Transaction:

    sender_onchain_address = context.get().config.vasp_address
    logger.info(
        f"=================Start external_offchain_transaction "
        f"{sender_onchain_address}, {sender_id}, {receiver_address}, {receiver_subaddress}, "
        f"{amount}, {currency}, {payment_type}"
    )
    if not validate_balance(sender_id, amount, currency):
        raise BalanceError(
            f"Balance {account_service.get_account_balance_by_id(account_id=sender_id).total[currency]} "
            f"is less than amount needed {amount}"
        )

    sender_subaddress = account_service.generate_new_subaddress(account_id=sender_id)
    logger.info(f"======sender_subaddress: {sender_subaddress}")
    ref_id = get_new_offchain_reference_id(sender_onchain_address)
    transaction = add_transaction(
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        status=TransactionStatus.PENDING,
        source_id=sender_id,
        source_address=sender_onchain_address,
        source_subaddress=sender_subaddress,
        destination_id=None,
        destination_address=receiver_address,
        destination_subaddress=receiver_subaddress,
        reference_id=ref_id,
    )

    # off-chain logic
    sender_address = LibraAddress.from_bytes(
        context.get().config.diem_address_hrp(),
        bytes.fromhex(sender_onchain_address),
        bytes.fromhex(sender_subaddress),
    )
    logger.info(
        f"sender address: {sender_onchain_address}, {sender_address.as_str()}, {sender_address.get_onchain().as_str()}"
    )
    receiver_address = LibraAddress.from_bytes(
        context.get().config.diem_address_hrp(),
        bytes.fromhex(receiver_address),
        bytes.fromhex(receiver_subaddress),
    )
    logger.info(
        f"receiver address: {receiver_address.as_str()}, {receiver_address.get_onchain().as_str()}",
    )
    sender = PaymentActor(
        sender_address.as_str(), StatusObject(Status.needs_kyc_data), [],
    )
    receiver = PaymentActor(receiver_address.as_str(), StatusObject(Status.none), [])
    action = PaymentAction(amount, currency, "charge", int(time()))
    reference_id = get_reference_id_from_transaction_id(transaction.id)
    payment = PaymentObject(
        sender=sender,
        receiver=receiver,
        reference_id=reference_id,
        original_payment_reference_id=original_payment_reference_id,
        description=description,
        action=action,
    )
    cmd = PaymentCommand(payment)

    if not get_transaction_status(transaction.id) == TransactionStatus.PENDING:
        logger.info(
            "In external_offchain_transaction, payment status is not PENDING, abort"
        )
        return

    update_transaction(transaction.id, TransactionStatus.OFF_CHAIN_STARTED)
    logger.info("In external_offchain_transaction: Updated status to OFF_CHAIN_STARTED")

    result = (
        offchain_client.get()
        .new_command(receiver_address.get_onchain(), cmd)
        .result(timeout=300)
    )
    logger.info(f"Offchain Result: {result}")

    return transaction


def start_settle_offchain(transaction_id: int) -> None:
    logger.info("~~~start_settle_offchain~~~")
    if services.run_bg_tasks():
        logger.info("start_settle_offchain asynchronous")
        from ..background_tasks.background import async_external_transaction_offchain

        async_external_transaction_offchain.send(transaction_id)
    else:
        logger.info("start_settle_offchain synchronous")
        settle_offchain(transaction_id)


def settle_offchain(transaction_id: int) -> None:
    transaction = get_transaction(transaction_id)
    logger.info(
        f"settle_offchain: {transaction_id}, "
        f"{transaction.status}, "
        f"{transaction.type}"
    )
    if (
        transaction.status == TransactionStatus.READY_FOR_ON_CHAIN
        and transaction.type == TransactionType.OFFCHAIN
    ):
        try:
            diem_currency = DiemCurrency[transaction.currency]
            logger.info(
                f"==============starting submit_onchain {diem_currency}, {transaction.amount}, "
                f"{transaction.destination_address}, {transaction.destination_subaddress}, "
                f"{transaction.source_subaddress}"
            )
            reference_id = get_reference_id_from_transaction_id(transaction_id)
            jsonrpc_txn = context.get().p2p_by_travel_rule(
                currency=diem_currency.value,
                amount=transaction.amount,
                receiver_vasp_address=transaction.destination_address,
                off_chain_reference_id=reference_id,
                metadata_signature=bytes.fromhex(
                    get_metadata_signature_from_reference_id(reference_id)
                ),
            )

            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.COMPLETED,
                sequence=jsonrpc_txn.transaction.sequence_number,
                blockchain_tx_version=jsonrpc_txn.version,
            )

            add_transaction_log(transaction_id, "On Chain Transfer Complete")
            log_execution("On Chain Transfer Complete")
        except Exception as e:
            logger.exception(f"Error in settle_offchain: {e}")
            add_transaction_log(transaction_id, "Off Chain Settlement Failed")
            log_execution("Off Chain Settlement Failed")
            update_transaction(
                transaction_id=transaction_id, status=TransactionStatus.CANCELED
            )


def submit_onchain(transaction_id: int) -> None:
    transaction = get_transaction(transaction_id)
    if transaction.status == TransactionStatus.PENDING:
        try:
            diem_currency = DiemCurrency[transaction.currency]

            jsonrpc_txn = context.get().p2p_by_general(
                currency=diem_currency.value,
                amount=transaction.amount,
                receiver_vasp_address=transaction.destination_address,
                receiver_sub_address=transaction.destination_subaddress,
                sender_sub_address=transaction.source_subaddress,
            )

            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.COMPLETED,
                sequence=jsonrpc_txn.transaction.sequence_number,
                blockchain_tx_version=jsonrpc_txn.version,
            )
            add_transaction_log(transaction_id, "On Chain Transfer Complete")
            log_execution("On Chain Transfer Complete")
        except Exception:
            logger.exception(f"Error in _async_start_onchain_transfer")
            add_transaction_log(transaction_id, "On Chain Transfer Failed")
            log_execution("On Chain Transfer Failed")
            update_transaction(
                transaction_id=transaction_id, status=TransactionStatus.CANCELED
            )


def get_total_balance() -> Balance:
    credits = get_total_currency_credits()
    debits = get_total_currency_debits()

    balance = Balance()
    for credit in credits:
        if credit.status == TransactionStatus.COMPLETED:
            balance.total[credit.currency] += credit.amount

    for debit in debits:
        if debit.status == TransactionStatus.PENDING:
            balance.frozen[debit.currency] += debit.amount
        if debit.status != TransactionStatus.CANCELED:
            balance.total[debit.currency] -= debit.amount

    return balance
