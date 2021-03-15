# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
import typing
from typing import Optional

import context
from diem import offchain
from diem.offchain import CommandType
from wallet.services.offchain.payment_command import (
    _process_payment_by_status,
    _lock_and_save_inbound_command,
    model_to_payment_command,
    update_model_base_on_payment_command,
    add_transaction_based_on_payment_command,
    _payment_command_status,
    _evaluate_kyc_data,
)
from wallet.services.offchain import utils
from wallet.services.offchain.fund_pull_pre_approval import (
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

from wallet.types import (
    TransactionStatus,
)

logger = logging.getLogger(__name__)


def process_inbound_command(
    request_sender_address: str, request_body_bytes: bytes
) -> (int, bytes):
    command = None
    try:
        command = utils.offchain_client().process_inbound_request(
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
    return code, offchain.jws.serialize(resp, utils.compliance_private_key().sign)


def process_offchain_tasks() -> None:
    def send_command(model) -> None:
        assert not model.inbound
        model.status = TransactionStatus.OFF_CHAIN_WAIT
        cmd = model_to_payment_command(model)
        utils.offchain_client().send_command(cmd, utils.compliance_private_key().sign)

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
            utils.offchain_client().send_command(cmd, utils.compliance_private_key().sign)
            logger.info(
                f"Submitting transaction base on command ref id:{model.reference_id} {model.amount} {model.currency}"
            )
            rpc_txn = context.get().p2p_by_travel_rule(
                cmd.receiver_account_address(utils.hrp()),
                cmd.payment.action.currency,
                cmd.payment.action.amount,
                cmd.travel_rule_metadata(utils.hrp()),
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
