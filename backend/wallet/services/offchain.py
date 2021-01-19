# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import typing
from dataclasses import dataclass
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
    FundsPullPreApprovalInvalidStatus,
    get_command_from_bech32,
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

from wallet.storage import funds_pull_pre_approval_command as fppa_storage

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
            handle_fund_pull_pre_approval_command(preapproval_command)

        return _jws(command.id())
    except offchain.Error as e:
        logger.exception(e)
        return _jws(command.id() if command else None, e.obj)


def handle_fund_pull_pre_approval_command(command):
    approval = command.funds_pull_pre_approval
    validate_expiration_timestamp(approval.scope.expiration_timestamp)
    role = get_role(approval)
    command_in_db = fppa_storage.get_command_by_id_and_role(
        approval.funds_pull_pre_approval_id, role
    )
    if command_in_db:
        validate_addresses(approval, command_in_db)
        validate_status(approval, command_in_db)
    if role == Role.PAYER:
        if approval.status == FundPullPreApprovalStatus.pending:
            if command_in_db:
                update_command(
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    )
                )
            else:
                address, sub_address = identifier.decode_account(
                    approval.address, _hrp()
                )

                commit_command(
                    preapproval_command_to_model(
                        account_id=get_account_id_from_subaddr(sub_address.hex()),
                        command=command,
                        role=Role.PAYER,
                    )
                )
        if approval.status in [
            FundPullPreApprovalStatus.valid,
            FundPullPreApprovalStatus.rejected,
        ]:
            raise FundsPullPreApprovalInvalidStatus()
        if approval.status == FundPullPreApprovalStatus.closed:
            if command_in_db:
                update_command(
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    )
                )
            else:
                raise FundsPullPreApprovalCommandNotFound()
    elif role == Role.PAYEE:
        if approval.status in [
            FundPullPreApprovalStatus.valid,
            FundPullPreApprovalStatus.rejected,
        ]:
            if command_in_db:
                if command_in_db.status == FundPullPreApprovalStatus.pending:
                    (
                        biller_address,
                        biller_sub_address,
                    ) = identifier.decode_account(approval.biller_address, _hrp())

                    update_command(
                        preapproval_command_to_model(
                            account_id=get_account_id_from_subaddr(
                                biller_sub_address.hex()
                            ),
                            command=command,
                            role=command_in_db.role,
                        )
                    )
                else:
                    raise FundsPullPreApprovalInvalidStatus()
            else:
                raise FundsPullPreApprovalCommandNotFound()
        if approval.status == FundPullPreApprovalStatus.closed:
            if command_in_db:
                update_command(
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    )
                )
            else:
                raise FundsPullPreApprovalCommandNotFound()
        if approval.status == FundPullPreApprovalStatus.pending:
            raise FundsPullPreApprovalInvalidStatus()


def all_combinations():
    statuses = [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]

    for incoming_status in statuses:
        for is_payee_address_mine in [True, False]:
            for is_payer_address_mine in [True, False]:
                for existing_status_as_payee in statuses + [None]:
                    for existing_status_as_payer in statuses + [None]:
                        yield Combination(
                            incoming_status,
                            is_payee_address_mine,
                            is_payer_address_mine,
                            existing_status_as_payee,
                            existing_status_as_payer,
                        )


def payee_and_payer_not_mine():
    return [
        combination
        for combination in all_combinations()
        if both_not_mine(combination)
    ]


def invalid_states():
    return [
        combination
        for combination in all_combinations()
        if (
            not combination.is_payee_address_mine
            and combination.existing_status_as_payee is not None
        )
        or (
            not combination.is_payer_address_mine
            and combination.existing_status_as_payer is not None
        )
    ]


def incoming_status_not_pending_and_no_records():
    return [
        combination
        for combination in all_combinations()
        if incoming_status_is_not_pending(combination) and both_no_records(combination)
    ]


def incoming_pending_for_payee():
    # if incoming status is 'pending', the payer address is not mine
    # and the payee address is mine all combinations are invalid
    return [
        combination
        for combination in all_combinations()
        if not combination.is_payer_address_mine
        and combination.is_payee_address_mine
        and incoming_status_is_pending(combination)
    ]


def incoming_valid_or_rejected_but_payee_not_pending():
    return [
        combination
        for combination in all_combinations()
        if incoming_status_is_valid_or_rejected(combination)
        and payee_status_is_not_pending(combination)
    ]


# both role are mine, incoming status is 'valid' or 'rejected',
# payee must be 'pending' and payer must be equals to incoming status
def incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming():
    return [
        combination
        for combination in all_combinations()
        if both_mine(combination)
        and incoming_status_is_valid_or_rejected(combination)
        and payee_status_is_pending(combination)
        and payer_status_equal_incoming_status(combination)
    ]


def incoming_status_is_valid_or_rejected(combination):
    return combination.incoming_status in [
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
    ]


# if both mine and incoming is pending payee must be pending and payer must be pending or None
# conditions:
# 1. both mine
# 2. incoming status is 'pending'
# 3. payee status is NOT 'pending' or it is 'pending' but payer is not
def incoming_pending_my_payee_not_pending_my_payer_pending_or_none():
    return [
        combination
        for combination in all_combinations()
        if both_mine(combination)
        and incoming_status_is_pending(combination)
        and (
            payee_status_is_not_pending(combination)
            or (
                payee_status_is_pending(combination)
                and (
                    payer_status_is_not_pending(combination)
                    or payer_status_is_not_none(combination)
                )
            )
        )
    ]


def incoming_closed_both_mine_one_must_be_closed_already():
    return [
        combination
        for combination in all_combinations()
        if both_mine(combination)
        and incoming_status_is_closed(combination)
        and payer_status_is_not_closed(combination)
        and payee_status_is_not_closed(combination)
    ]


def both_not_mine(combination):
    return not combination.is_payee_address_mine and not combination.is_payer_address_mine


def both_no_records(combination):
    return (
        combination.existing_status_as_payer is None
        and combination.existing_status_as_payee is None
    )


def payee_status_is_not_closed(combination):
    return combination.existing_status_as_payee is not FundPullPreApprovalStatus.closed


def payer_status_is_not_closed(combination):
    return combination.existing_status_as_payer is not FundPullPreApprovalStatus.closed


def incoming_status_is_not_pending(combination):
    return combination.incoming_status is not FundPullPreApprovalStatus.pending


def payer_status_equal_incoming_status(combination):
    return combination.existing_status_as_payer != combination.incoming_status


def payer_status_is_not_none(combination):
    return combination.existing_status_as_payer is not None


def payer_status_is_not_pending(combination):
    return combination.existing_status_as_payer is not FundPullPreApprovalStatus.pending


def payee_status_is_not_pending(combination):
    return combination.existing_status_as_payee is not FundPullPreApprovalStatus.pending


def payee_status_is_pending(combination):
    return combination.existing_status_as_payee is FundPullPreApprovalStatus.pending


def incoming_status_is_pending(combination):
    return combination.incoming_status is FundPullPreApprovalStatus.pending


def incoming_status_is_closed(combination):
    return combination.incoming_status is FundPullPreApprovalStatus.closed


def both_mine(combination):
    return combination.is_payer_address_mine and combination.is_payee_address_mine


def make_error_combinations(combinations) -> dict:
    return {combination: None for combination in combinations}


@dataclass(frozen=True)
class Combination:
    incoming_status: str  # 4
    is_payee_address_mine: bool  # 2
    is_payer_address_mine: bool  # 2
    existing_status_as_payee: Optional[str]  # 5
    existing_status_as_payer: Optional[str]  # 5


def get_role_2():
    Incoming = FundPullPreApprovalStatus
    Existing = FundPullPreApprovalStatus
    explicit_combinations = {
        Combination(
            Incoming.pending, True, True, Existing.pending, None
        ): Role.PAYER,  # new request from known payee
        Combination(
            Incoming.pending, True, True, Existing.pending, Existing.pending
        ): Role.PAYER,  # update request from known payee
        Combination(
            Incoming.pending, False, True, None, None
        ): Role.PAYER,  # new request from unknown payee
        Combination(
            Incoming.pending, False, True, None, Existing.pending
        ): Role.PAYER,  # update request from unknown payee
        Combination(Incoming.pending, False, True, None, Existing.valid): None,
        Combination(Incoming.pending, False, True, None, Existing.closed): None,
        Combination(Incoming.pending, False, True, None, Existing.rejected): None,
        Combination(
            Incoming.valid, True, False, Existing.pending, None
        ): Role.PAYEE,  # approve request by unknown payer
        Combination(
            Incoming.valid, True, True, Existing.pending, Existing.valid
        ): Role.PAYEE,
        Combination(
            Incoming.rejected, True, False, Existing.pending, None
        ): Role.PAYEE,  # reject request by unknown payer
        Combination(
            Incoming.rejected, True, True, Existing.pending, Existing.rejected
        ): Role.PAYEE,
        Combination(
            Incoming.closed, False, True, None, Existing.pending
        ): Role.PAYER,  # close 'pending' request by unknown payee
        Combination(
            Incoming.closed, False, True, None, Existing.valid
        ): Role.PAYER,  # close 'valid' request by unknown payee
        Combination(
            Incoming.closed, True, True, Existing.closed, Existing.rejected
        ): None,  # can't close rejected request
        Combination(
            Incoming.closed, True, True, Existing.rejected, Existing.closed
        ): None,  # can't close rejected request
        Combination(
            Incoming.closed, True, True, Existing.closed, Existing.pending
        ): Role.PAYER,  # close request by payee
        Combination(
            Incoming.closed, True, True, Existing.pending, Existing.closed
        ): Role.PAYEE,  # close request by payer
        Combination(
            Incoming.closed, True, True, Existing.closed, Existing.valid
        ): Role.PAYER,  # close request by payee
        Combination(
            Incoming.closed, True, True, Existing.valid, Existing.closed
        ): Role.PAYEE,  # close request by payer
        Combination(Incoming.closed, True, True, None, Existing.closed): None,
        #
        Combination(
            Incoming.closed, True, True, Existing.closed, Existing.closed
        ): None,
        Combination(Incoming.closed, True, True, Existing.closed, None): None,
        #
        Combination(Incoming.closed, True, False, Existing.closed, None): None,
        Combination(Incoming.closed, True, False, Existing.rejected, None): None,
        Combination(Incoming.closed, True, False, Existing.pending, None): Role.PAYEE,
        Combination(Incoming.closed, True, False, Existing.valid, None): Role.PAYEE,
        #
        Combination(Incoming.closed, False, True, None, Existing.rejected): None,
        Combination(Incoming.closed, False, True, None, Existing.closed): None,
    }

    explicit_combinations.update(make_error_combinations(payee_and_payer_not_mine()))
    explicit_combinations.update(make_error_combinations(invalid_states()))
    explicit_combinations.update(
        make_error_combinations(incoming_status_not_pending_and_no_records())
    )
    explicit_combinations.update(make_error_combinations(incoming_pending_for_payee()))
    explicit_combinations.update(
        make_error_combinations(incoming_valid_or_rejected_but_payee_not_pending())
    )
    explicit_combinations.update(
        make_error_combinations(
            incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming()
        )
    )
    explicit_combinations.update(
        make_error_combinations(
            incoming_pending_my_payee_not_pending_my_payer_pending_or_none()
        )
    )
    explicit_combinations.update(
        make_error_combinations(incoming_closed_both_mine_one_must_be_closed_already())
    )

    return explicit_combinations


# If no record was found in DB then the incoming command is completely new
# and therefore we can assume that we received it as PAYER
#     # the side who sending the command is saving his update before he send it,
#     # therefore we can assume that the side which is not have the updated status is the active role
# TODO if approval.status == 'pending' compare all values to decide ?
def get_role(approval):
    biller_address, biller_sub_address = identifier.decode_account(
        approval.biller_address, _hrp()
    )
    address, sub_address = identifier.decode_account(approval.address, _hrp())
    payee_command = get_command_from_bech32(
        approval.biller_address, approval.funds_pull_pre_approval_id
    )
    payer_command = get_command_from_bech32(
        approval.address, approval.funds_pull_pre_approval_id
    )

    combination = Combination(
        incoming_status=approval.status,
        is_payee_address_mine=is_my_address(biller_address),
        is_payer_address_mine=is_my_address(address),
        existing_status_as_payee=payee_command.funds_pull_pre_approval.status
        if payee_command is not None
        else None,
        existing_status_as_payer=payer_command.funds_pull_pre_approval.status
        if payer_command is not None
        else None,
    )

    combinations = get_role_2()

    role = combinations.get(combination)

    if role is None:
        raise FundsPullPreApprovalError()

    return role


def is_my_address(address):
    return address.to_hex() == _vasp_address()


def validate_status(approval, command_in_db):
    if command_in_db.status in [
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]:
        raise FundsPullPreApprovalInvalidStatus
    if (
        command_in_db.status == approval.status
        and command_in_db.status != FundPullPreApprovalStatus.pending
    ):
        raise FundsPullPreApprovalInvalidStatus


def validate_addresses(approval, command_in_db):
    if (
        approval.address != command_in_db.address
        or approval.biller_address != command_in_db.biller_address
    ):
        raise ValueError("address and biller_addres values are immutable")


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


def _vasp_address():
    return context.get().config.vasp_address


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
