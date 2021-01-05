# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple, Callable, List, Dict

import context
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import offchain, identifier
from diem.offchain import (
    CommandType,
    FundPullPreApprovalStatus,
    ScopedCumulativeAmountObject,
    CurrencyObject,
    FundPullPreApprovalScopeObject,
    FundPullPreApprovalType,
    FundPullPreApprovalObject,
    FundPullPreApprovalCommandObject,
    CommandRequestObject,
)
from diem_utils.types.currencies import DiemCurrency
from wallet import storage
from wallet.services import account, kyc

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_commands import (
    get_account_commands,
    update_command,
    FundsPullPreApprovalCommandNotFound,
    commit_command,
)
from wallet.storage.models import FundsPullPreApprovalCommands

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
        _lock_and_save_inbound_command(command)
        return _jws(command.cid)
    except offchain.Error as e:
        logger.exception(e)
        return _jws(command.cid if command else None, e.obj)


def _jws(cid: Optional[str], err: Optional[offchain.OffChainErrorObject] = None):
    code = 400 if err else 200
    resp = offchain.reply_request(cid)
    return (code, offchain.jws.serialize(resp, _compliance_private_key().sign))


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

    _process_by_status(TransactionStatus.OFF_CHAIN_OUTBOUND, send_command)
    _process_by_status(TransactionStatus.OFF_CHAIN_INBOUND, offchain_action)
    _process_by_status(TransactionStatus.OFF_CHAIN_READY, submit_txn)


def _process_by_status(
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


def get_funds_pull_pre_approvals(account_id: int) -> List[FundsPullPreApprovalCommands]:
    return get_account_commands(account_id)


def approve_funds_pull_pre_approval(funds_pre_approval_id: str, status: str) -> None:
    update_command(funds_pre_approval_id, status)

    # TODO update in offchain client


def establish_funds_pull_pre_approval(
    account_id: int,
    biller_address: str,
    funds_pre_approval_id: str,
    scope_type: str,
    expiration_timestamp: int,
    max_cumulative_unit: str = None,
    max_cumulative_unit_value: int = None,
    max_cumulative_amount: int = None,
    max_cumulative_amount_currency: str = None,
    max_transaction_amount: int = None,
    max_transaction_amount_currency: str = None,
    description: str = None,
) -> None:
    """ Establish funds pull pre approval by payer """
    vasp_address = context.get().config.vasp_address
    sub_address = account.generate_new_subaddress(account_id)
    hrp = context.get().config.diem_address_hrp()
    address = identifier.encode_account(vasp_address, sub_address, hrp)

    commit_command(
        FundsPullPreApprovalCommands(
            account_id=account_id,
            address=address,
            biller_address=biller_address,
            funds_pre_approval_id=funds_pre_approval_id,
            scope_type=scope_type,
            expiration_timestamp=expiration_timestamp,
            max_cumulative_unit=max_cumulative_unit,
            max_cumulative_unit_value=max_cumulative_unit_value,
            max_cumulative_amount=max_cumulative_amount,
            max_cumulative_amount_currency=max_cumulative_amount_currency,
            max_transaction_amount=max_transaction_amount,
            max_transaction_amount_currency=max_transaction_amount_currency,
            description=description,
            status=FundPullPreApprovalStatus.valid,
        )
    )

    max_cumulative_amount_object = ScopedCumulativeAmountObject(
        unit=max_cumulative_unit,
        value=max_cumulative_unit_value,
        max_amount=CurrencyObject(
            amount=max_cumulative_amount, currency=max_cumulative_amount_currency
        ),
    )

    scope_object = FundPullPreApprovalScopeObject(
        type=FundPullPreApprovalType.consent,
        expiration_timestamp=expiration_timestamp,
        max_cumulative_amount=max_cumulative_amount_object,
        max_transaction_amount=CurrencyObject(
            amount=max_transaction_amount, currency=max_transaction_amount_currency
        ),
    )

    fund_pull_pre_approval = FundPullPreApprovalObject(
        address=address,
        biller_address=biller_address,
        funds_pre_approval_id=funds_pre_approval_id,
        scope=scope_object,
        description=description,
        status=FundPullPreApprovalStatus.valid,
    )

    command = FundPullPreApprovalCommandObject(
        _ObjectType=CommandType.FundPullPreApprovalCommand,
        fund_pull_pre_approval=fund_pull_pre_approval,
    )

    cid = str(uuid.UUID())

    command_object = CommandRequestObject(
        cid=cid,
        command_type=CommandType.FundPullPreApprovalCommand,
        command=command,
    )

    # TODO generate CommandRequestObject and send through offchain client
