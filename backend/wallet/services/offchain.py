# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import typing
from datetime import datetime
from typing import Optional, Tuple, Callable, List, Dict

import context
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import offchain, identifier
from diem.offchain import (
    CommandType,
    FundPullPreApprovalStatus,
)
from diem_utils.types.currencies import DiemCurrency
from wallet import storage
from wallet.services import account, kyc
from wallet.services.fund_pull_pre_approval import (
    preapproval_command_to_model,
    validate_expiration_timestamp,
    process_funds_pull_pre_approvals_requests,
    Role,
    FundsPullPreApprovalError,
)

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_command import (
    get_account_commands,
    FundsPullPreApprovalCommandNotFound,
    commit_command,
    get_commands_by_sent_status,
    get_command_by_id,
    update_command,
)

from ..storage import (
    lock_for_update,
    commit_transaction,
    get_transactions_by_status,
    get_account_id_from_subaddr,
    Transaction,
)
from ..types import (
    TransactionType,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


def save_outbound_transaction(
    sender_id: int,
    destination_address: str,
    destination_subaddress: str,
    amount: int,
    currency: DiemCurrency,
) -> Transaction:
    sender_onchain_address = context.get().config.vasp_address
    sender_subaddress = account.generate_new_subaddress(account_id=sender_id)
    return commit_transaction(
        _new_payment_command_transaction(
            offchain.PaymentCommand.init(
                identifier.encode_account(
                    sender_onchain_address, sender_subaddress, _hrp()
                ),
                _user_kyc_data(sender_id),
                identifier.encode_account(
                    destination_address, destination_subaddress, _hrp()
                ),
                amount,
                currency.value,
            ),
            TransactionStatus.OFF_CHAIN_OUTBOUND,
        )
    )


def process_inbound_command(
    request_sender_address: str, request_body_bytes: bytes
) -> (int, bytes):
    command = None
    try:
        command = _offchain_client().process_inbound_request(
            request_sender_address, request_body_bytes
        )

        if command.command_type() == CommandType.PaymentCommand:
            payment_command = typing.cast(offchain.PaymentCommand, command)
            _lock_and_save_inbound_command(payment_command)
        elif command.command_type() == CommandType.FundPullPreApprovalCommand:
            preapproval_command = typing.cast(
                offchain.FundsPullPreApprovalCommand, command
            )
            approval = preapproval_command.funds_pull_pre_approval

            validate_expiration_timestamp(approval.scope.expiration_timestamp)

            command_in_db = get_command_by_id(approval.funds_pull_pre_approval_id)

            if command_in_db:
                validate_addresses(approval, command_in_db)
                # update existing command only if incoming status and existing status are 'pending',
                # otherwise - raise error
                if (
                    approval.status == FundPullPreApprovalStatus.pending
                    and command_in_db.status == FundPullPreApprovalStatus.pending
                ):
                    update_command(
                        preapproval_command_to_model(
                            account_id=command_in_db.account_id,
                            command=preapproval_command,
                            role=command_in_db.role,
                        )
                    )
                else:
                    raise FundsPullPreApprovalError(
                        "Can't update existing command unless the status is 'pending'"
                    )
            else:
                role = get_role_by_command_status(approval.status)
                commit_command(
                    preapproval_command_to_model(
                        account_id=account.get_account_id_from_bech32(approval.address),
                        command=preapproval_command,
                        role=role,
                    )
                )

        return _jws(command.id())
    except offchain.Error as e:
        logger.exception(e)
        return _jws(command.id() if command else None, e.obj)


def validate_addresses(approval, command_in_db):
    if (
        approval.address != command_in_db.address
        or approval.biller_address != command_in_db.biller_address
    ):
        raise ValueError("address and biller_addres values are immutable")


def get_role_by_command_status(status):
    if status is None or status == FundPullPreApprovalStatus.pending:
        return Role.PAYER
    elif status in [
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
    ]:
        return Role.PAYEE
    else:
        raise FundsPullPreApprovalError(f"Wrong status {status} for incoming request")


def _jws(cid: Optional[str], err: Optional[offchain.OffChainErrorObject] = None):
    code = 400 if err else 200
    resp = offchain.reply_request(cid)
    return code, offchain.jws.serialize(resp, _compliance_private_key().sign)


def process_offchain_tasks() -> None:
    def send_command(txn, cmd, _) -> None:
        assert not cmd.is_inbound()
        txn.status = TransactionStatus.OFF_CHAIN_WAIT
        _offchain_client().send_command(cmd, _compliance_private_key().sign)

    def offchain_action(txn, cmd, action) -> None:
        assert cmd.is_inbound()
        if action is None:
            return
        if action == offchain.Action.EVALUATE_KYC_DATA:
            new_cmd = _evaluate_kyc_data(cmd)
            txn.command_json = offchain.to_json(new_cmd)
            txn.status = _command_transaction_status(
                new_cmd, TransactionStatus.OFF_CHAIN_OUTBOUND
            )
        else:
            # todo: handle REVIEW_KYC_DATA and CLEAR_SOFT_MATCH
            raise ValueError(f"unsupported offchain action: {action}, command: {cmd}")

    def submit_txn(txn, cmd, _) -> Transaction:
        if cmd.is_sender():
            logger.info(
                f"Submitting transaction ID:{txn.id} {txn.amount} {txn.currency}"
            )
            _offchain_client().send_command(cmd, _compliance_private_key().sign)
            rpc_txn = context.get().p2p_by_travel_rule(
                cmd.receiver_account_address(_hrp()),
                cmd.payment.action.currency,
                cmd.payment.action.amount,
                cmd.travel_rule_metadata(_hrp()),
                bytes.fromhex(cmd.payment.recipient_signature),
            )
            txn.sequence = rpc_txn.transaction.sequence_number
            txn.blockchain_version = rpc_txn.version
            txn.status = TransactionStatus.COMPLETED
            logger.info(
                f"Submitted transaction ID:{txn.id} V:{txn.blockchain_version} {txn.amount} {txn.currency}"
            )

    _process_payment_by_status(TransactionStatus.OFF_CHAIN_OUTBOUND, send_command)
    _process_payment_by_status(TransactionStatus.OFF_CHAIN_INBOUND, offchain_action)
    _process_payment_by_status(TransactionStatus.OFF_CHAIN_READY, submit_txn)
    process_funds_pull_pre_approvals_requests()


def _process_payment_by_status(
    status: TransactionStatus,
    callback: Callable[
        [Transaction, offchain.PaymentCommand, offchain.Action], Optional[Transaction]
    ],
) -> None:
    txns = get_transactions_by_status(status)
    for txn in txns:
        cmd = _txn_payment_command(txn)
        action = cmd.follow_up_action()

        def callback_with_status_check(txn):
            if txn.status == status:
                callback(txn, cmd, action)
            return txn

        logger.info(f"lock for update: {action} {cmd}")
        try:
            lock_for_update(txn.reference_id, callback_with_status_check)
        except Exception:
            logger.exception("process offchain transaction failed")


def _evaluate_kyc_data(command: offchain.PaymentObject) -> offchain.PaymentObject:
    # todo: evaluate command.opponent_actor_obj().kyc_data
    # when pass evaluation, we send kyc data as receiver or ready for settlement as sender
    if command.is_receiver():
        return _send_kyc_data_and_receipient_signature(command)
    return command.new_command(status=offchain.Status.ready_for_settlement)


def _send_kyc_data_and_receipient_signature(
    command: offchain.PaymentCommand,
) -> offchain.PaymentCommand:
    sig_msg = command.travel_rule_metadata_signature_message(_hrp())
    user_id = get_account_id_from_subaddr(command.receiver_subaddress(_hrp()).hex())

    return command.new_command(
        recipient_signature=_compliance_private_key().sign(sig_msg).hex(),
        kyc_data=_user_kyc_data(user_id),
        status=offchain.Status.ready_for_settlement,
    )


def _lock_and_save_inbound_command(command: offchain.PaymentCommand) -> Transaction:
    def validate_and_save(txn: Optional[Transaction]) -> Transaction:
        if txn:
            prior = _txn_payment_command(txn)
            if command == prior:
                return
            command.validate(prior)
            txn.command_json = offchain.to_json(command)
            txn.status = _command_transaction_status(
                command, TransactionStatus.OFF_CHAIN_INBOUND
            )
        else:
            txn = _new_payment_command_transaction(
                command, TransactionStatus.OFF_CHAIN_INBOUND
            )
        return txn

    return lock_for_update(command.reference_id(), validate_and_save)


def _command_transaction_status(
    command: offchain.PaymentCommand, default: TransactionStatus
) -> TransactionStatus:
    if command.is_both_ready():
        return TransactionStatus.OFF_CHAIN_READY
    elif command.is_abort():
        return TransactionStatus.CANCELED
    return default


def _new_payment_command_transaction(
    command: offchain.PaymentCommand, status: TransactionStatus
) -> Transaction:
    payment = command.payment
    sender_address, source_subaddress = _account_address_and_subaddress(
        payment.sender.address
    )
    destination_address, destination_subaddress = _account_address_and_subaddress(
        payment.receiver.address
    )
    source_id = get_account_id_from_subaddr(source_subaddress)
    destination_id = get_account_id_from_subaddr(destination_subaddress)

    return Transaction(
        type=TransactionType.OFFCHAIN,
        status=status,
        amount=payment.action.amount,
        currency=payment.action.currency,
        created_timestamp=datetime.utcnow(),
        source_id=source_id,
        source_address=sender_address,
        source_subaddress=source_subaddress,
        destination_id=destination_id,
        destination_address=destination_address,
        destination_subaddress=destination_subaddress,
        reference_id=command.reference_id(),
        command_json=offchain.to_json(command),
    )


def _account_address_and_subaddress(account_id: str) -> Tuple[str, Optional[str]]:
    account_address, sub = identifier.decode_account(
        account_id, context.get().config.diem_address_hrp()
    )
    return (account_address.to_hex(), sub.hex() if sub else None)


def _user_kyc_data(user_id: int) -> offchain.KycDataObject:
    return offchain.types.from_json_obj(
        kyc.get_user_kyc_info(user_id), offchain.KycDataObject, ""
    )


def _txn_payment_command(txn: Transaction) -> offchain.PaymentCommand:
    return offchain.from_json(txn.command_json, offchain.PaymentCommand)


def _offchain_client() -> offchain.Client:
    return context.get().offchain_client


def _compliance_private_key() -> Ed25519PrivateKey:
    return context.get().config.compliance_private_key()


def _hrp() -> str:
    return context.get().config.diem_address_hrp()


def get_payment_command_json(transaction_id: int) -> Optional[Dict]:
    transaction = storage.get_transaction(transaction_id)

    if transaction and transaction.command_json:
        return json.loads(transaction.command_json)

    return None


def get_account_payment_commands(account_id: int) -> List[Dict]:
    transactions = storage.get_account_transactions(account_id)
    commands = []

    for transaction in transactions:
        command_json = transaction.command_json

        if command_json:
            commands.append(json.loads(command_json))

    return commands
