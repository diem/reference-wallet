# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import dataclass
from typing import Optional

import context
import wallet.services.offchain.p2p_payment as pc_service
from diem import diem_types, offchain, identifier, jsonrpc, txnmetadata
from diem_utils.types.currencies import DiemCurrency
from wallet.services import (
    account as account_service,
)
from wallet.services.risk import risk_check
from wallet.storage import Transaction

from . import INVENTORY_ACCOUNT_NAME
from .log import add_transaction_log
from .. import services
from ..logging import log_execution
from wallet import storage
from ..types import (
    TransactionDirection,
    TransactionType,
    TransactionStatus,
    BalanceError,
    Balance,
    to_refund_reason,
)

logger = logging.getLogger(name="wallet-service:transaction")


class RiskCheckError(Exception):
    pass


class SelfAsDestinationError(Exception):
    pass


class InvalidTravelRuleMetadata(Exception):
    pass


class InvalidRefundMetadata(Exception):
    pass


class P2MTxnRegistrationError(Exception):
    pass


# submit transaction on-chain using p2m metadata.
# recipient signature is needed only if the amount >= 1000 (travel rule)
# input example: ref-id: 1c5ee1eb-559b-48b3-898c-85b4d4713890,
#               amount: 100000000,
#               currency: XUS,
#               recipient_signature: None,
#               receiver_address: tdm1paue4j3fqr6nzl5xglqr337surful4nmrx6kn9fgmh5qz6
def put_p2m_txn_onchain(
    reference_id: str,
    amount: int,
    currency: str,
    receiver_address_bech32: str,
    recipient_signature: str = None,
) -> jsonrpc.Transaction:

    logger.info(
        f"submitting P2M transaction: "
        f"ref-id: {reference_id}, "
        f"amount: {amount}, "
        f"currency: {currency}, "
        f"recipient_signature: {recipient_signature}, "
        f"receiver_address: {receiver_address_bech32}"
    )

    metadata_bytes = txnmetadata.payment_metadata(reference_id)

    recipient_signature_bytes = b""
    if recipient_signature is not None:
        recipient_signature_bytes = bytes.fromhex(recipient_signature)

    hrp = context.get().config.diem_address_hrp()
    receiver_account_address = identifier.decode_account_address(
        receiver_address_bech32, hrp
    )

    return context.get().p2p_by_travel_rule(
        receiver_account_address,
        currency,
        amount,
        metadata_bytes,
        recipient_signature_bytes,
    )


# register p2m transaction on block-chain and database
def submit_p2m_transaction(payment_model, account_id, recipient_signature):
    try:
        txn = put_p2m_txn_onchain(
            payment_model.reference_id,
            payment_model.amount,
            payment_model.currency,
            payment_model.vasp_address,
            recipient_signature,
        )

        logger.info(
            f"p2m txn submitted, "
            f"sequnce-number: {txn.transaction.sequence_number}, "
            f"txn-version: {txn.version}"
        )

        storage.add_transaction(
            amount=payment_model.amount,
            currency=DiemCurrency[payment_model.currency],
            payment_type=TransactionType.OFFCHAIN,
            status=TransactionStatus.COMPLETED,
            source_id=account_id,
            source_address=payment_model.my_address,
            source_subaddress=None,
            destination_id=None,
            destination_address=payment_model.vasp_address,
            destination_subaddress=None,
            sequence=txn.transaction.sequence_number,
            blockchain_version=txn.version,
            reference_id=payment_model.reference_id,
        )
    except Exception as e:
        error = P2MTxnRegistrationError(e)
        logger.error(error)
        raise error


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

    logger.info(f"METADATA {metadata}")

    if isinstance(metadata, diem_types.Metadata__GeneralMetadata) and isinstance(
        metadata.value, diem_types.GeneralMetadata__GeneralMetadataVersion0
    ):
        logger.info(
            f"process_incoming_transaction general metadata [{blockchain_version}]: "
            f"sender: {sender_address}, receiver: {receiver_address}, "
            f"seq: {sequence}, amount: {amount}"
        )
        logger.info("general metadata")
        general_v0 = metadata.value.value

        if general_v0.from_subaddress:
            sender_subaddress = general_v0.from_subaddress.hex()

        if storage.get_transaction_by_details(
            source_address=sender_address,
            source_subaddress=sender_subaddress,
            sequence=sequence,
        ):
            log_execution(
                f"Incoming transaction sequence {sequence} already exists. Aborting"
            )
            return

        if general_v0.to_subaddress:
            receiver_subaddr = general_v0.to_subaddress.hex()
        else:
            logger.info(
                f"process_incoming_transaction general metadata credit inventory [{blockchain_version}]: "
                f"sender: {sender_address}, receiver: {receiver_address}, "
                f"seq: {sequence}, amount: {amount}"
            )
            storage.add_transaction(
                amount=amount,
                currency=currency,
                payment_type=TransactionType.EXTERNAL,
                status=TransactionStatus.COMPLETED,
                source_address=sender_address,
                source_subaddress=sender_subaddress,
                destination_id=storage.get_account(
                    account_name=INVENTORY_ACCOUNT_NAME
                ).id,
                destination_address=receiver_address,
                destination_subaddress=receiver_subaddr,
                sequence=sequence,
                blockchain_version=blockchain_version,
            )
            return

        receiver_id = storage.get_account_id_from_subaddr(receiver_subaddr)

        # Could not find receiver for the given non-zero subaddress, so send back a refund from inventory account
        if receiver_id is None:
            logger.info(
                f"Could not find receiver for the given subaddress {receiver_subaddr}, sending back refund to "
                f"sender address: {sender_address} and sender_subaddress: {sender_subaddress}, amount {amount}, "
                f"blockchain version {blockchain_version}, seq {sequence}"
            )
            # Record the received transaction as a regular transaction to inventory account
            inventory_account_id = storage.get_account(
                account_name=INVENTORY_ACCOUNT_NAME
            ).id
            tx = storage.add_transaction(
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
        else:
            logger.info(
                f"Regular general metadata transaction with receiver ID {receiver_id}, "
                f"sender address: {sender_address} and sender_subaddress: {sender_subaddress}, amount {amount}, "
                f"blockchain version {blockchain_version}, seq {sequence}"
            )
            storage.add_transaction(
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

        payment_command = storage.get_payment_command(reference_id)

        payment_command_sender_address, _ = identifier.decode_account(
            payment_command.sender_address, context.get().config.diem_address_hrp()
        )
        payment_command_receiver_address, _ = identifier.decode_account(
            payment_command.receiver_address, context.get().config.diem_address_hrp()
        )
        payment_command_receiver_address_hex = payment_command_receiver_address.to_hex()
        payment_command_sender_address_hex = payment_command_sender_address.to_hex()
        if (
            payment_command.amount == amount
            and payment_command.status == TransactionStatus.OFF_CHAIN_READY
            and payment_command_sender_address_hex == sender_address
            and payment_command_receiver_address_hex == receiver_address
        ):
            transaction = pc_service.add_transaction_based_on_payment_command(
                command=pc_service.model_to_payment_command(payment_command),
                status=TransactionStatus.COMPLETED,
                sequence=sequence,
                blockchain_version=blockchain_version,
            )
            payment_command.status = TransactionStatus.COMPLETED
            storage.save_payment_command(payment_command)

            logger.info(f"transaction completed: {transaction.id}")

            return

        raise InvalidTravelRuleMetadata(
            f"Travel Rule metadata decode failed: PaymentCommand {payment_command} "
            f"with reference ID {reference_id} should have amount: {payment_command.amount}, "
            f"status: {TransactionStatus.OFF_CHAIN_READY}, sender address: {payment_command.sender_address}, "
            f"receiver address: {payment_command.receiver_address}, but received transaction has amount: {amount}, "
            f"status: {payment_command.status}, sender address: {sender_address}, receiver address: {receiver_address}"
        )

    if isinstance(metadata, diem_types.Metadata__RefundMetadata) and isinstance(
        metadata.value, diem_types.RefundMetadata__RefundMetadataV0
    ):
        logger.info(
            f"process_incoming_transaction refund metadata [{blockchain_version}]: "
            f"sender: {sender_address}, receiver: {receiver_address}, "
            f"seq: {sequence}, amount: {amount}"
        )
        txn_version = int(metadata.value.value.transaction_version)
        reason = metadata.value.value.reason

        logger.info(f"Refund metadata: txn version: {txn_version}, reason: {reason}")

        original_txn = storage.get_transaction_by_blockchain_version(txn_version)

        logger.info(f"Refund metadata: original txn id: {original_txn}")

        # Cannot find the referred original transaction
        if original_txn is None:
            logger.info(
                f"Refund metadata invalid: txn version: {txn_version} does not exist"
            )
            # Record the received transaction as a regular transaction to inventory account
            inventory_account_id = storage.get_account(
                account_name=INVENTORY_ACCOUNT_NAME
            ).id
            storage.add_transaction(
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

        refund_reason = to_refund_reason(reason)
        original_txn = storage.get_transaction_by_blockchain_version(txn_version)
        receiver_id = original_txn.source_id
        receiver_subaddr = original_txn.source_subaddress
        sender_subaddress = original_txn.destination_subaddress
        original_txn_id = original_txn.id

        if storage.get_transaction_by_details(
            source_address=sender_address,
            source_subaddress=sender_subaddress,
            sequence=sequence,
        ):
            log_execution(
                f"Incoming transaction sequence {sequence} already exists. Aborting"
            )
            return

        storage.add_transaction(
            amount=amount,
            currency=currency,
            payment_type=TransactionType.REFUND,
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


def send_transaction(
    sender_id: int,
    amount: int,
    currency: DiemCurrency,
    destination_address: str,
    destination_subaddress: Optional[str] = None,
    payment_type: Optional[TransactionType] = None,
    original_txn_id: Optional[str] = None,
) -> Optional[str]:
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
        ).id
    else:
        if not risk_check(sender_id, amount):
            payment_command = pc_service.save_outbound_payment_command(
                sender_id=sender_id,
                destination_address=destination_address,
                destination_subaddress=destination_subaddress,
                amount=amount,
                currency=currency,
            )
            return payment_command.reference_id()

        return _send_transaction_external(
            sender_id=sender_id,
            destination_address=destination_address,
            destination_subaddress=destination_subaddress,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
            original_txn_id=original_txn_id,
        ).id


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
        original_txn_id=original_txn_id,
    )


def _send_transaction_internal(
    sender_id, destination_subaddress, payment_type, amount, currency
) -> Optional[Transaction]:
    log_execution(
        f"internal transfer from {sender_id} to receiver {destination_subaddress}"
    )
    receiver_id = storage.get_account_id_from_subaddr(subaddr=destination_subaddress)
    payment_type = TransactionType.INTERNAL if payment_type is None else payment_type

    return internal_transaction(
        sender_id=sender_id,
        receiver_id=receiver_id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
    )


def update_transaction(
    transaction_id: str,
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


@dataclass
class FundsTransfer:
    transaction: Transaction
    payment_command: offchain.PaymentCommand


def get_funds_transfer(reference_id: str) -> FundsTransfer:
    return FundsTransfer(
        transaction=storage.get_transaction(reference_id),
        payment_command=pc_service.get_payment_command(reference_id=reference_id),
    )


def get_transaction(
    transaction_id: Optional[str] = None, blockchain_version: Optional[int] = None
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

    transaction = storage.add_transaction(
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
    original_txn_id: str,
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

    transaction = storage.add_transaction(
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


def submit_onchain(transaction_id: str) -> None:
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
                original_txn_version = get_transaction(
                    transaction.original_txn_id
                ).blockchain_version
                jsonrpc_txn = context.get().p2p_by_refund(
                    currency=diem_currency.value,
                    amount=transaction.amount,
                    receiver_vasp_address=transaction.destination_address,
                    original_txn_version=original_txn_version,
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
    credits = storage.get_total_currency_credits()
    debits = storage.get_total_currency_debits()

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
