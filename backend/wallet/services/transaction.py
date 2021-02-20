# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from diem import diem_types, jsonrpc, txnmetadata
from diem_utils.types.currencies import DiemCurrency
from wallet.services import (
    account as account_service,
    kyc,
    offchain as offchain_service,
)
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
    get_transaction_status,
    get_transaction_by_reference_id,
    get_transaction_by_blockchain_version,
)
from ..storage import get_account_id_from_subaddr, get_account
from ..types import (
    TransactionDirection,
    TransactionType,
    TransactionStatus,
    BalanceError,
    Balance,
    RefundReason,
)

import context, logging

logger = logging.getLogger(name="wallet-service:transaction")


class RiskCheckError(Exception):
    pass


class SelfAsDestinationError(Exception):
    pass


class InvalidTravelRuleMetadata(Exception):
    pass


class InvalidRefundMetadata(Exception):
    pass


def decode_general_metadata_v0(
    metadata_bytes: bytes,
) -> Optional[diem_types.GeneralMetadataV0]:
    metadata = diem_types.Metadata.bcs_deserialize(metadata_bytes)

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
        f"process_incoming_transaction[{blockchain_version}]: sender: {sender_address}, receiver: {receiver_address}, "
        f"seq: {sequence}, amount: {amount}"
    )
    log_execution("Attempting to process incoming transaction from chain")
    receiver_id = None
    sender_subaddress = None
    receiver_subaddr = None
    original_txn_id = None
    refund_reason = None
    payment_type = None

    logger.info(f"METADATA {metadata}")

    if isinstance(metadata, diem_types.Metadata__GeneralMetadata) and isinstance(
        metadata.value, diem_types.GeneralMetadata__GeneralMetadataVersion0
    ):
        logger.info(
            f"process_incoming_transaction general metadata [{blockchain_version}]: "
            f"sender: {sender_address}, receiver: {receiver_address}, "
            f"seq: {sequence}, amount: {amount}"
        )
        payment_type = TransactionType.EXTERNAL
        logger.info("general metadata")
        general_v0 = metadata.value.value

        if general_v0.to_subaddress:
            receiver_subaddr = general_v0.to_subaddress.hex()
            receiver_id = get_account_id_from_subaddr(receiver_subaddr)
        else:
            # Subaddress was not specified, so route the fund to inventory account
            receiver_id = get_account(account_name=INVENTORY_ACCOUNT_NAME).id

        if general_v0.from_subaddress:
            sender_subaddress = general_v0.from_subaddress.hex()

    if isinstance(metadata, diem_types.Metadata__TravelRuleMetadata) and isinstance(
        metadata.value, diem_types.TravelRuleMetadata__TravelRuleMetadataVersion0
    ):
        logger.info(
            f"process_incoming_transaction travel rule metadata [{blockchain_version}]: "
            f"sender: {sender_address}, receiver: {receiver_address}, "
            f"seq: {sequence}, amount: {amount}"
        )
        travel_rule_v0 = metadata.value.value
        reference_id = travel_rule_v0.off_chain_reference_id
        logger.info(f"travel rule metadata reference id: {reference_id}")

        if reference_id is None:
            raise InvalidTravelRuleMetadata(
                f"Invalid Travel Rule metadata : reference_id None"
            )

        transaction = get_transaction_by_reference_id(reference_id)
        if (
            transaction.amount == amount
            and transaction.status == TransactionStatus.OFF_CHAIN_READY
            and transaction.source_address == sender_address
            and transaction.destination_address == receiver_address
        ):
            logger.info(f"transaction completed: {transaction.id}")
            update_transaction(
                transaction_id=transaction.id,
                status=TransactionStatus.COMPLETED,
                sequence=sequence,
                blockchain_tx_version=blockchain_version,
            )

            return

        raise InvalidTravelRuleMetadata(
            f"Travel Rule metadata decode failed: Transaction {transaction.id} with reference ID {reference_id} "
            f"should have amount: {transaction.amount}, status: {TransactionStatus.OFF_CHAIN_READY}, "
            f"source address: {transaction.source_address}, destination address: {transaction.destination_address},"
            f" but received transaction has amount: {amount}, status: {transaction.status}, "
            f"source address: {sender_address}, destination address: {receiver_address}"
        )

    if isinstance(metadata, diem_types.Metadata__RefundMetadata) and isinstance(
        metadata.value, diem_types.RefundMetadata__RefundMetadataV0
    ):
        logger.info(
            f"process_incoming_transaction refund metadata [{blockchain_version}]: "
            f"sender: {sender_address}, receiver: {receiver_address}, "
            f"seq: {sequence}, amount: {amount}"
        )
        txn_version = metadata.value.value.transaction_version
        reason = metadata.value.value.reason
        payment_type = TransactionType.REFUND

        original_txn = get_transaction_by_blockchain_version(txn_version)

        logger.info(f"Refund metadata: txn version: {txn_version}, reason: {reason}")

        # Cannot find the referred original transaction
        if original_txn is None:
            logger.info(
                f"Refund metadata invalid: txn version: {txn_version} does not exist"
            )
            # Record the received transaction as a regular transaction to inventory account
            inventory_account_id = get_account(account_name=INVENTORY_ACCOUNT_NAME).id
            add_transaction(
                amount=amount,
                currency=currency,
                payment_type=TransactionType.EXTERNAL,
                status=TransactionStatus.FAILED,
                source_address=sender_address,
                destination_id=inventory_account_id,
                destination_address=receiver_address,
                sequence=sequence,
                blockchain_version=blockchain_version,
            )
            return

        if isinstance(reason, diem_types.RefundReason__InvalidSubaddress):
            refund_reason = RefundReason.INVALID_SUBADDRESS
        elif isinstance(reason, diem_types.RefundReason__UserInitiatedPartialRefund):
            refund_reason = RefundReason.USER_INITIATED_PARTIAL_REFUND
        elif isinstance(reason, diem_types.RefundReason__UserInitiatedFullRefund):
            refund_reason = RefundReason.USER_INITIATED_FULL_REFUND
        else:
            refund_reason = RefundReason.OTHER

        original_txn = get_transaction_by_blockchain_version(txn_version)
        receiver_id = original_txn.source_id
        receiver_subaddr = original_txn.source_subaddress
        sender_subaddress = original_txn.destination_subaddress
        original_txn_id = original_txn.id

    # Could not find receiver for the given subaddress, so send back a refund from inventory account
    if receiver_id is None:
        logger.info(
            f"Could not find receiver for the given subaddress {receiver_subaddr}, sending back refund to "
            f"sender address: {sender_address} and sender_subaddress: {sender_subaddress}, amount {amount}"
        )
        # Record the received transaction as a regular transaction to inventory account
        inventory_account_id = get_account(account_name=INVENTORY_ACCOUNT_NAME).id
        tx = add_transaction(
            amount=amount,
            currency=currency,
            payment_type=TransactionType.EXTERNAL,
            status=TransactionStatus.NEED_REFUND,
            source_address=sender_address,
            source_subaddress=sender_subaddress,
            destination_id=inventory_account_id,
            destination_address=receiver_address,
            sequence=sequence,
            blockchain_version=blockchain_version,
        )
        send_transaction(
            sender_id=inventory_account_id,
            amount=amount,
            currency=currency,
            destination_address=sender_address,
            destination_subaddress=sender_subaddress,
            payment_type=TransactionType.REFUND,
            original_txn_id=tx.id,
        )
        return

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
        payment_type=payment_type,
        status=TransactionStatus.COMPLETED,
        source_address=sender_address,
        source_subaddress=sender_subaddress,
        destination_id=receiver_id,
        destination_address=receiver_address,
        destination_subaddress=receiver_subaddr,
        sequence=sequence,
        blockchain_version=blockchain_version,
        original_txn_id=original_txn_id,
        refund_reason=refund_reason,
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
    original_txn_id: Optional[int] = None,
) -> Optional[Transaction]:
    log_execution(
        f"transfer from sender {sender_id} to receiver (dest addr: {destination_address} subaddr: {destination_subaddress})"
    )

    if account_service.is_own_address(
        sender_id=sender_id,
        receiver_vasp=destination_address,
        receiver_subaddress=destination_subaddress,
    ):
        raise SelfAsDestinationError(
            "It is not possible to send transaction to your own wallet."
        )

    if destination_subaddress is None:
        return _unhosted_wallet_transfer(
            sender_id=sender_id, destination_address=destination_address
        )

    if not validate_balance(sender_id, amount, currency):
        raise BalanceError(
            f"Balance {account_service.get_account_balance_by_id(account_id=sender_id).total[currency]} "
            f"is less than amount needed {amount}"
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
        if not risk_check(sender_id, amount):
            return offchain_service.save_outbound_transaction(
                sender_id=sender_id,
                destination_address=destination_address,
                destination_subaddress=destination_subaddress,
                amount=amount,
                currency=currency,
            )

        return _send_transaction_external(
            sender_id=sender_id,
            destination_address=destination_address,
            destination_subaddress=destination_subaddress,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
            original_txn_id=original_txn_id,
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
    original_txn_id,
) -> Optional[Transaction]:
    log_execution(
        f"external transfer type {payment_type} from {sender_id} to receiver {destination_address}, "
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
        original_txn_id=original_txn_id,
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
    original_txn_id: int,
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

    sender_subaddress = None
    if (
        payment_type == TransactionType.EXTERNAL
        or payment_type == TransactionType.REFUND
    ):
        sender_subaddress = account_service.generate_new_subaddress(
            account_id=sender_id
        )

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
        original_txn_id=original_txn_id,
    )

    if services.run_bg_tasks():
        from ..background_tasks.background import async_external_transaction

        async_external_transaction.send(transaction.id)
    else:
        submit_onchain(transaction_id=transaction.id)

    return transaction


def submit_onchain(transaction_id: int) -> None:
    transaction = get_transaction(transaction_id)
    if transaction.status == TransactionStatus.PENDING:
        try:
            diem_currency = DiemCurrency[transaction.currency]

            if transaction.type == TransactionType.EXTERNAL:
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
                add_transaction_log(
                    transaction_id, "On Chain Transfer of General Txn Complete"
                )
                log_execution(
                    "On chain transfer complete "
                    f"txid: {transaction_id} "
                    f"v: {jsonrpc_txn.version} "
                )

            if transaction.type == TransactionType.REFUND:
                jsonrpc_txn = context.get().p2p_by_refund(
                    currency=diem_currency.value,
                    amount=transaction.amount,
                    receiver_vasp_address=transaction.destination_address,
                    txn_version=transaction.original_txn_id,
                )
                update_transaction(
                    transaction_id=transaction_id,
                    status=TransactionStatus.COMPLETED,
                    sequence=jsonrpc_txn.transaction.sequence_number,
                    blockchain_tx_version=jsonrpc_txn.version,
                )
                add_transaction_log(
                    transaction_id, "On Chain Transfer of Refund Txn Complete"
                )
                log_execution(
                    "On chain transfer complete "
                    f"txid: {transaction_id} "
                    f"v: {jsonrpc_txn.version} "
                )

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
