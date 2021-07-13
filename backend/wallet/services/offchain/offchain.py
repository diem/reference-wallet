# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
import typing

import context
import offchain
from offchain import CommandType
from wallet.services.kyc import xstr
from wallet.services.offchain import utils
from wallet.services.offchain.fund_pull_pre_approval import (
    process_funds_pull_pre_approvals_requests,
    handle_fund_pull_pre_approval_command,
)
from wallet.services.offchain.p2m_payment_as_receiver import (
    handle_incoming_get_payment_info_request,
    handle_init_charge_command,
    handle_init_authorize_command,
    handle_abort_payment_command,
)
from wallet.services.offchain.p2p_payment import (
    process_payment_by_status,
    lock_and_save_inbound_command,
    model_to_payment_command,
    update_model_base_on_payment_command,
    add_transaction_based_on_payment_command,
    payment_command_status,
)

# noinspection PyUnresolvedReferences
from wallet.services.offchain.p2p_payment_as_receiver import (
    save_payment_command_as_receiver,
)
from wallet.services.offchain.utils import evaluate_kyc_data
from wallet.types import (
    TransactionStatus,
)

logger = logging.getLogger(__name__)


def process_inbound_command(
    request_sender_address: str,
    request_body_bytes: bytes,
) -> (int, bytes):
    command = None
    try:
        request = utils.offchain_client().deserialize_jws_request(
            request_sender_address, request_body_bytes
        )

        # LRW as RECEIVER
        if request.command_type == CommandType.GetPaymentInfo:
            return handle_incoming_get_payment_info_request(request)
        elif request.command_type == CommandType.InitChargePayment:
            return handle_init_charge_command(request)
        elif request.command_type == CommandType.InitAuthorizeCommand:
            return handle_init_authorize_command(request)
        elif request.command_type == CommandType.AbortPayment:
            return handle_abort_payment_command(request)

        command = utils.offchain_client().process_inbound_request(
            request, request_sender_address
        )

        logger.info(f"process inbound command: {command}")
        logger.debug(f"process inbound command: {offchain.to_json(command)}")

        if command.command_type() == CommandType.PaymentCommand:
            payment_command = typing.cast(offchain.PaymentCommand, command)
            if payment_command.is_sender():
                logger.debug(f"process inbound command as SENDER")
                lock_and_save_inbound_command(payment_command)
            else:
                logger.debug(f"process inbound command as RECEIVER")
                save_payment_command_as_receiver(payment_command)

        elif command.command_type() == CommandType.FundPullPreApprovalCommand:
            preapproval_command = typing.cast(
                offchain.FundsPullPreApprovalCommand, command
            )
            handle_fund_pull_pre_approval_command(preapproval_command)

        return utils.jws_response(command.id())
    except offchain.Error as e:
        logger.exception(e)
        return utils.jws_response(command.id() if command else None, e.obj)


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

        logger.info(
            f"handling offchain_action reference_id: {model.reference_id}, "
            f"sender address: {model.sender_address}, "
            f"sender status: {model.sender_status}, "
            f"receiver address: {model.receiver_address}, "
            f"receiver status: {model.receiver_status}, "
            f"action: {action}"
        )

        if action is None:
            return
        if action == offchain.Action.EVALUATE_KYC_DATA:
            new_cmd = evaluate_kyc_data(cmd)
            status = payment_command_status(
                new_cmd, TransactionStatus.OFF_CHAIN_OUTBOUND
            )
            update_model_base_on_payment_command(model, new_cmd, status)
        else:
            # todo: handle REVIEW_KYC_DATA and CLEAR_SOFT_MATCH
            raise ValueError(f"unsupported offchain action: {action}, command: {cmd}")

    def submit_txn(model) -> None:
        if model.sender_address == model.my_actor_address:
            cmd = model_to_payment_command(model)
            utils.offchain_client().send_command(
                cmd, utils.compliance_private_key().sign
            )
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

    def send_command_as_receiver(model) -> None:
        payment_command = model_to_payment_command(model)
        kyc_data = {
            "payload_version": 1,
            "type": "individual",
            "given_name": xstr("Bond"),
            "surname": xstr("Marton"),
            "dob": xstr("2010-21-01"),
            "address": {
                "city": xstr("Dogcity"),
                "country": xstr("Dogland"),
                "line1": xstr("1234 Puppy Street"),
                "line2": xstr("dogpalace 3"),
                "postal_code": xstr("123456"),
                "state": xstr("Dogstate"),
            },
        }

        if not model.recipient_signature:
            sig_msg = payment_command.travel_rule_metadata_signature_message(
                utils.hrp()
            )
        else:
            sig_msg = model.recipient_signature

        new_command = payment_command.new_command(
            recipient_signature=utils.compliance_private_key().sign(sig_msg).hex(),
            kyc_data=kyc_data,
            status=offchain.Status.ready_for_settlement,
            inbound=payment_command.inbound,
        )

        update_model_base_on_payment_command(
            model, new_command, TransactionStatus.OFF_CHAIN_WAIT
        )

        utils.offchain_client().send_command(
            new_command, utils.compliance_private_key().sign
        )

    process_payment_by_status(TransactionStatus.OFF_CHAIN_OUTBOUND, send_command)
    process_payment_by_status(TransactionStatus.OFF_CHAIN_INBOUND, offchain_action)
    process_payment_by_status(TransactionStatus.OFF_CHAIN_READY, submit_txn)
    process_payment_by_status(
        TransactionStatus.OFF_CHAIN_RECEIVER_OUTBOUND, send_command_as_receiver
    )
    process_funds_pull_pre_approvals_requests()
