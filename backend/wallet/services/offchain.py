# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
import typing
from datetime import datetime
from typing import Optional, Tuple, Callable, List

import context
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import offchain, identifier
from diem.offchain import CommandType
from diem_utils.types.currencies import DiemCurrency
from wallet import storage
from wallet.services import account, kyc
from wallet.storage import models
from wallet.services.fund_pull_pre_approval import (
    process_funds_pull_pre_approvals_requests,
    handle_fund_pull_pre_approval_command,
)

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_command import (
    get_account_commands,
    FundsPullPreApprovalCommandNotFound,
    commit_command,
    get_commands_by_sent_status,
    get_command_by_id,
    update_command,
    get_account_command_by_id,
)

from ..storage import (
    lock_for_update,
    get_account_id_from_subaddr,
    Transaction,
    save_payment_command,
)
from ..types import (
    TransactionType,
    TransactionStatus,
)

logger = logging.getLogger(__name__)

PaymentCommandModel = models.PaymentCommand


def save_outbound_payment_command(
    sender_id: int,
    destination_address: str,
    destination_subaddress: str,
    amount: int,
    currency: DiemCurrency,
) -> offchain.PaymentCommand:
    sender_onchain_address = context.get().config.vasp_address
    sender_sub_address = account.generate_new_subaddress(account_id=sender_id)

    command = offchain.PaymentCommand.init(
        identifier.encode_account(sender_onchain_address, sender_sub_address, _hrp()),
        _user_kyc_data(sender_id),
        identifier.encode_account(destination_address, destination_subaddress, _hrp()),
        amount,
        currency.value,
    )

    save_payment_command(
        payment_command_to_model(command, TransactionStatus.OFF_CHAIN_OUTBOUND)
    )

    return command


def process_inbound_command(
    request_sender_address: str, request_body_bytes: bytes
) -> (int, bytes):
    command = None
    try:
        command = _offchain_client().process_inbound_request(
            request_sender_address, request_body_bytes
        )
        logger.info(f"process inbound command: {offchain.to_json(command)}")

        if command.command_type() == CommandType.PaymentCommand:
            payment_command = typing.cast(offchain.PaymentCommand, command)
            _lock_and_save_inbound_command(payment_command)
        elif command.command_type() == CommandType.FundPullPreApprovalCommand:
            preapproval_command = typing.cast(
                offchain.FundsPullPreApprovalCommand, command
            )
            handle_fund_pull_pre_approval_command(preapproval_command)

        return _jws(command.id())
    except offchain.Error as e:
        logger.exception(e)
        return _jws(command.cid if command else None, e.obj)


def _jws(cid: Optional[str], err: Optional[offchain.OffChainErrorObject] = None):
    code = 400 if err else 200
    resp = offchain.reply_request(cid)
    return code, offchain.jws.serialize(resp, _compliance_private_key().sign)


def process_offchain_tasks() -> None:
    def send_command(model) -> None:
        assert not model.inbound
        model.status = TransactionStatus.OFF_CHAIN_WAIT
        cmd = model_to_payment_command(model)
        _offchain_client().send_command(cmd, _compliance_private_key().sign)

    def offchain_action(model) -> None:
        assert model.inbound
        cmd = model_to_payment_command(model)
        action = cmd.follow_up_action()

        if action is None:
            return
        if action == offchain.Action.EVALUATE_KYC_DATA:
            new_cmd = _evaluate_kyc_data(cmd)
            status = _payment_command_status(
                new_cmd, TransactionStatus.OFF_CHAIN_OUTBOUND
            )
            update_model_base_on_payment_command(model, new_cmd, status)
        else:
            # todo: handle REVIEW_KYC_DATA and CLEAR_SOFT_MATCH
            raise ValueError(f"unsupported offchain action: {action}, command: {cmd}")

    def submit_txn(model) -> None:
        if model.sender_address == model.my_actor_address:
            cmd = model_to_payment_command(model)
            _offchain_client().send_command(cmd, _compliance_private_key().sign)
            logger.info(
                f"Submitting transaction base on command ref id:{model.reference_id} {model.amount} {model.currency}"
            )
            rpc_txn = context.get().p2p_by_travel_rule(
                cmd.receiver_account_address(_hrp()),
                cmd.payment.action.currency,
                cmd.payment.action.amount,
                cmd.travel_rule_metadata(_hrp()),
                bytes.fromhex(cmd.payment.recipient_signature),
            )
            transaction = add_transaction_based_on_payment_command(
                command=cmd,
                status=TransactionStatus.COMPLETED,
                sequence=rpc_txn.transaction.sequence_number,
                blockchain_version=rpc_txn.version,
            )
            logger.info(
                f"Submitted transaction ID:{transaction.id} V:{transaction.blockchain_version} {transaction.amount} {transaction.currency}"
            )
            model.status = TransactionStatus.COMPLETED

    _process_payment_by_status(TransactionStatus.OFF_CHAIN_OUTBOUND, send_command)
    _process_payment_by_status(TransactionStatus.OFF_CHAIN_INBOUND, offchain_action)
    _process_payment_by_status(TransactionStatus.OFF_CHAIN_READY, submit_txn)
    process_funds_pull_pre_approvals_requests()


def _process_payment_by_status(
    status: TransactionStatus,
    callback: Callable[[PaymentCommandModel], Optional[PaymentCommandModel]],
) -> None:
    commands_models = storage.get_payment_commands_by_status(status)
    for model in commands_models:

        def callback_with_status_check(model):
            if model.status == status:
                callback(model)
            return model

        logger.info(f"lock for update: {model}")
        try:
            lock_for_update(model.reference_id, callback_with_status_check)
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


def _lock_and_save_inbound_command(
    command: offchain.PaymentCommand,
) -> None:
    def validate_and_save(model: Optional[PaymentCommandModel]) -> PaymentCommandModel:
        if model:
            prior = get_payment_command(model.reference_id)
            if command == prior:
                return
            command.validate(prior)
            status = _payment_command_status(
                command, TransactionStatus.OFF_CHAIN_INBOUND
            )
            update_model_base_on_payment_command(model, command, status)
        else:
            model = payment_command_to_model(
                command, TransactionStatus.OFF_CHAIN_INBOUND
            )
        return model

    lock_for_update(command.reference_id(), validate_and_save)


def _payment_command_status(
    command: offchain.PaymentCommand, default: TransactionStatus
) -> TransactionStatus:
    if command.is_both_ready():
        return TransactionStatus.OFF_CHAIN_READY
    elif command.is_abort():
        return TransactionStatus.CANCELED
    return default


def add_transaction_based_on_payment_command(
    command: offchain.PaymentCommand,
    status: TransactionStatus,
    sequence: int,
    blockchain_version: int,
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

    reference_id = command.reference_id()

    return storage.add_transaction(
        amount=payment.action.amount,
        currency=DiemCurrency[payment.action.currency],
        payment_type=TransactionType.OFFCHAIN,
        status=status,
        source_id=source_id,
        source_address=sender_address,
        source_subaddress=source_subaddress,
        destination_id=destination_id,
        destination_address=destination_address,
        destination_subaddress=destination_subaddress,
        sequence=sequence,
        blockchain_version=blockchain_version,
        reference_id=reference_id,
    )


def _account_address_and_subaddress(account_id: str) -> Tuple[str, Optional[str]]:
    account_address, sub = identifier.decode_account(
        account_id, context.get().config.diem_address_hrp()
    )
    return account_address.to_hex(), sub.hex() if sub else None


def _user_kyc_data(user_id: int) -> offchain.KycDataObject:
    return offchain.types.from_dict(
        kyc.get_user_kyc_info(user_id), offchain.KycDataObject, ""
    )


def _offchain_client() -> offchain.Client:
    return context.get().offchain_client


def _compliance_private_key() -> Ed25519PrivateKey:
    return context.get().config.compliance_private_key()


def _hrp() -> str:
    return context.get().config.diem_address_hrp()


def get_payment_command(reference_id: str) -> Optional[offchain.PaymentCommand]:
    payment_command = storage.get_payment_command(reference_id)

    if payment_command:
        return model_to_payment_command(payment_command)

    return None


def get_account_payment_commands(account_id: int) -> List[offchain.PaymentCommand]:
    commands_models = storage.get_account_payment_commands(account_id)
    commands = []

    for model in commands_models:
        commands.append(model_to_payment_command(model))

    return commands


def update_model_base_on_payment_command(
    model: PaymentCommandModel, command: offchain.PaymentCommand, status
):
    model.my_actor_address = command.my_actor_address
    model.inbound = command.is_inbound()
    model.sender_address = command.payment.sender.address
    model.sender_status = command.payment.sender.status.status
    model.sender_kyc_data = (
        offchain.to_json(command.payment.sender.kyc_data)
        if command.payment.sender.kyc_data
        else None
    )
    model.sender_metadata = command.payment.sender.metadata
    model.sender_additional_kyc_data = command.payment.sender.additional_kyc_data
    model.receiver_address = command.payment.receiver.address
    model.receiver_status = command.payment.receiver.status.status
    model.receiver_kyc_data = (
        offchain.to_json(command.payment.receiver.kyc_data)
        if command.payment.receiver.kyc_data
        else None
    )
    model.receiver_metadata = command.payment.receiver.metadata
    model.receiver_additional_kyc_data = command.payment.receiver.additional_kyc_data
    model.action = command.payment.action.action
    model.recipient_signature = command.payment.recipient_signature
    if status:
        model.status = status


def payment_command_to_model(
    command: offchain.PaymentCommand, status: TransactionStatus
) -> PaymentCommandModel:
    return models.PaymentCommand(
        my_actor_address=command.my_actor_address,
        inbound=command.inbound,
        cid=command.cid,
        reference_id=command.payment.reference_id,
        sender_address=command.payment.sender.address,
        sender_status=command.payment.sender.status.status,
        sender_kyc_data=offchain.to_json(command.payment.sender.kyc_data)
        if command.payment.sender.kyc_data
        else None,
        sender_metadata=command.payment.sender.metadata,
        sender_additional_kyc_data=command.payment.sender.additional_kyc_data,
        receiver_address=command.payment.receiver.address,
        receiver_status=command.payment.receiver.status.status,
        receiver_kyc_data=offchain.to_json(command.payment.receiver.kyc_data)
        if command.payment.receiver.kyc_data
        else None,
        receiver_metadata=command.payment.receiver.metadata,
        receiver_additional_kyc_data=command.payment.receiver.additional_kyc_data,
        amount=command.payment.action.amount,
        currency=command.payment.action.currency,
        action=command.payment.action.action,
        created_at=datetime.fromtimestamp(command.payment.action.timestamp),
        original_payment_reference_id=command.payment.original_payment_reference_id,
        recipient_signature=command.payment.recipient_signature,
        description=command.payment.description,
        status=status,
        account_id=get_command_account_id(command),
    )


def get_command_account_id(command: offchain.PaymentCommand) -> int:
    """ Find the account id for the command """
    sender_address_bech32 = command.payment.sender.address
    sender_address, sender_sub_address = identifier.decode_account(
        sender_address_bech32, context.get().config.diem_address_hrp()
    )

    if sender_address.to_hex() == context.get().config.vasp_address:
        account_id = get_account_id_from_subaddr(sender_sub_address.hex())
        if account_id:
            return account_id

    receiver_address_bech32 = command.payment.receiver.address
    receiver_address, receiver_sub_address = identifier.decode_account(
        receiver_address_bech32, context.get().config.diem_address_hrp()
    )

    if receiver_address.to_hex() == context.get().config.vasp_address:
        account_id = get_account_id_from_subaddr(receiver_sub_address.hex())
        if account_id:
            return account_id

    # TODO inventory account id? error?
    return 1


def model_to_payment_command(model: PaymentCommandModel) -> offchain.PaymentCommand:
    return offchain.PaymentCommand(
        my_actor_address=model.my_actor_address,
        inbound=True if model.status == TransactionStatus.OFF_CHAIN_INBOUND else False,
        cid=model.cid,
        payment=offchain.PaymentObject(
            reference_id=model.reference_id,
            sender=offchain.PaymentActorObject(
                address=model.sender_address,
                status=offchain.StatusObject(status=model.sender_status),
                kyc_data=offchain.from_json(
                    model.sender_kyc_data, offchain.KycDataObject
                )
                if model.sender_kyc_data
                else None,
                # TODO
                metadata=model.sender_metadata,
                additional_kyc_data=model.sender_additional_kyc_data,
            ),
            receiver=offchain.PaymentActorObject(
                address=model.receiver_address,
                status=offchain.StatusObject(status=model.receiver_status),
                kyc_data=offchain.from_json(
                    model.receiver_kyc_data, offchain.KycDataObject
                )
                if model.receiver_kyc_data
                else None,
                # TODO
                metadata=model.receiver_metadata,
                additional_kyc_data=model.receiver_additional_kyc_data,
            ),
            action=offchain.PaymentActionObject(
                amount=model.amount,
                currency=model.currency,
                action=model.action,
                timestamp=int(datetime.timestamp(model.created_at)),
            ),
            original_payment_reference_id=model.original_payment_reference_id,
            recipient_signature=model.recipient_signature,
            description=model.description,
        ),
    )
