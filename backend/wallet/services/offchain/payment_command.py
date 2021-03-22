import logging
from datetime import datetime
from typing import Optional, Callable, List

import context
import offchain
from diem import identifier, txnmetadata
from offchain import Status
from diem_utils.types.currencies import DiemCurrency
from wallet import storage
from wallet.services import account
from wallet.services.offchain.utils import (
    hrp,
    account_address_and_subaddress,
    user_kyc_data,
    compliance_private_key,
    generate_my_address,
    PaymentCommandModel,
)
from wallet.storage import models
from wallet.storage import (
    save_payment_command,

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_command import (
    get_account_commands,
    FundsPullPreApprovalCommandNotFound,
    commit_command,
    update_command,
)
from wallet.types import TransactionStatus, TransactionType

from ..storage import (
    lock_for_update,
    get_account_id_from_subaddr,
    Transaction,
)

logger = logging.getLogger(__name__)


def add_payment_command_as_sender(
    account_id,
    reference_id,
    vasp_address,
    merchant_name,
    action,
    currency,
    amount,
    expiration: int,
) -> None:
    my_address = generate_my_address(account_id)

    sig_msg = txnmetadata.travel_rule(
        reference_id, identifier.decode_account_address(my_address, hrp()), amount
    )[1]

    payment_command = models.PaymentCommand(
        my_actor_address=my_address,
        inbound=False,
        cid=reference_id,
        reference_id=reference_id,
        sender_address=my_address,
        sender_status=Status.none,
        sender_kyc_data=offchain.to_json(user_kyc_data(account_id)),
        receiver_address=vasp_address,
        receiver_status=Status.none,
        amount=amount,
        currency=currency,
        action=action,
        created_at=datetime.now(),
        status=TransactionStatus.PENDING,
        account_id=account_id,
        merchant_name=merchant_name,
        expiration=datetime.fromtimestamp(expiration),
        recipient_signature=compliance_private_key().sign(sig_msg).hex(),
    )
    save_payment_command(payment_command)


def update_payment_command_sender_status(reference_id, status):
    storage.update_payment_command_sender_status(reference_id, status)


def get_payment_command(reference_id: str) -> Optional[offchain.PaymentCommand]:
    payment_command = storage.get_payment_command(reference_id)

    if payment_command:
        return model_to_payment_command(payment_command)

    return None


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


def _lock_and_save_inbound_command(
    command: offchain.PaymentCommand,
) -> None:
    def validate_and_save(model: Optional[PaymentCommandModel]) -> PaymentCommandModel:
        if model:
            prior_model = storage.get_payment_command(model.reference_id)
            # if command status is pending and not contain sender_address we assume that
            # LRW is playing the merchant role in this offchain conversation as part
            # of validation test and therefore we set the sender_address as the sender_address
            # in the incoming command
            if (
                prior_model.status == TransactionStatus.PENDING
                and not prior_model.sender_address
            ):
                prior_model.sender_address = command.payment.sender.address

            prior = model_to_payment_command(prior_model)

            logger.info(
                f"#######################################################################"
            )
            logger.info(f"~~~~~~ prior:   {prior}")
            logger.info(f"~~~~~~ command: {command}")
            logger.info(
                f"#######################################################################"
            )
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


def payment_command_to_model(
    command: offchain.PaymentCommand, status: TransactionStatus
) -> PaymentCommandModel:
    return models.PaymentCommand(
        my_actor_address=command.my_actor_address,
        inbound=command.inbound,
        cid=command.reference_id(),
        reference_id=command.reference_id(),
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


def get_account_payment_commands(account_id: int) -> List[offchain.PaymentCommand]:
    commands_models = storage.get_account_payment_commands(account_id)
    commands = []

    for model in commands_models:
        commands.append(model_to_payment_command(model))

    return commands


def add_transaction_based_on_payment_command(
    command: offchain.PaymentCommand,
    status: TransactionStatus,
    sequence: int,
    blockchain_version: int,
) -> Transaction:
    payment = command.payment
    sender_address, source_subaddress = account_address_and_subaddress(
        payment.sender.address
    )
    destination_address, destination_subaddress = account_address_and_subaddress(
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
        identifier.encode_account(sender_onchain_address, sender_sub_address, hrp()),
        user_kyc_data(sender_id),
        identifier.encode_account(destination_address, destination_subaddress, hrp()),
        amount,
        currency.value,
    )

    save_payment_command(
        payment_command_to_model(command, TransactionStatus.OFF_CHAIN_OUTBOUND)
    )

    return command


def _payment_command_status(
    command: offchain.PaymentCommand, default: TransactionStatus
) -> TransactionStatus:
    if command.is_both_ready():
        return TransactionStatus.OFF_CHAIN_READY
    elif command.is_abort():
        return TransactionStatus.CANCELED
    return default


def _evaluate_kyc_data(command: offchain.PaymentObject) -> offchain.PaymentObject:
    # todo: evaluate command.opponent_actor_obj().kyc_data
    # when pass evaluation, we send kyc data as receiver or ready for settlement as sender
    if command.is_receiver():
        return _send_kyc_data_and_receipient_signature(command)
    return command.new_command(status=offchain.Status.ready_for_settlement)


def _send_kyc_data_and_receipient_signature(
    command: offchain.PaymentCommand,
) -> offchain.PaymentCommand:
    sig_msg = command.travel_rule_metadata_signature_message(hrp())
    user_id = get_account_id_from_subaddr(command.receiver_subaddress(hrp()).hex())

    return command.new_command(
        recipient_signature=compliance_private_key().sign(sig_msg).hex(),
        kyc_data=user_kyc_data(user_id),
        status=offchain.Status.ready_for_settlement,
    )


def get_funds_pull_pre_approvals(
    account_id: int,
) -> List[models.FundsPullPreApprovalCommand]:
    return get_account_commands(account_id)


def approve_funds_pull_pre_approval(
    funds_pull_pre_approval_id: str, status: str
) -> None:
    """ update command in db with new given status and role PAYER"""
    if status not in ["valid", "rejected"]:
        raise ValueError(f"Status must be 'valid' or 'rejected' and not '{status}'")

    command = get_funds_pull_pre_approval_command(funds_pull_pre_approval_id)

    if command:
        if command.status != "pending":
            raise RuntimeError(
                f"Could not approve command with status {command.status}"
            )
        update_command(funds_pull_pre_approval_id, status, Role.PAYER)
    else:
        raise RuntimeError(f"Could not find command {funds_pull_pre_approval_id}")


def establish_funds_pull_pre_approval(
    account_id: int,
    biller_address: str,
    funds_pull_pre_approval_id: str,
    funds_pull_pre_approval_type: str,
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
    validate_expiration_timestamp(expiration_timestamp)

    command = get_funds_pull_pre_approval_command(funds_pull_pre_approval_id)

    if command is not None:
        raise RuntimeError(
            f"Command with id {funds_pull_pre_approval_id} already exist in db"
        )

    vasp_address = context.get().config.vasp_address
    sub_address = account.generate_new_subaddress(account_id)
    hrp = context.get().config.diem_address_hrp()
    address = identifier.encode_account(vasp_address, sub_address, hrp)

    commit_command(
        models.FundsPullPreApprovalCommand(
            account_id=account_id,
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type=funds_pull_pre_approval_type,
            expiration_timestamp=expiration_timestamp,
            max_cumulative_unit=max_cumulative_unit,
            max_cumulative_unit_value=max_cumulative_unit_value,
            max_cumulative_amount=max_cumulative_amount,
            max_cumulative_amount_currency=max_cumulative_amount_currency,
            max_transaction_amount=max_transaction_amount,
            max_transaction_amount_currency=max_transaction_amount_currency,
            description=description,
            status=FundPullPreApprovalStatus.valid,
            role=Role.PAYER,
        )
    )


def preapproval_model_to_command(
    command: models.FundsPullPreApprovalCommand, my_address: str
):
    funds_pull_pre_approval = offchain.FundPullPreApprovalObject(
        funds_pull_pre_approval_id=command.funds_pull_pre_approval_id,
        address=command.address,
        biller_address=command.biller_address,
        scope=offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=command.expiration_timestamp,
            max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                unit=command.max_cumulative_unit,
                value=command.max_cumulative_unit_value,
                max_amount=offchain.CurrencyObject(
                    amount=command.max_cumulative_amount,
                    currency=command.max_cumulative_amount_currency,
                ),
            ),
            max_transaction_amount=offchain.CurrencyObject(
                amount=command.max_transaction_amount,
                currency=command.max_transaction_amount_currency,
            ),
        ),
        status=command.status,
        description=command.description,
    )

    return offchain.FundsPullPreApprovalCommand(
        my_actor_address=my_address,
        funds_pull_pre_approval=funds_pull_pre_approval,
    )


def preapproval_command_to_model(
    account_id, command: offchain.FundsPullPreApprovalCommand, role: str
) -> models.FundsPullPreApprovalCommand:
    preapproval_object = command.funds_pull_pre_approval
    max_cumulative_amount = preapproval_object.scope.max_cumulative_amount
    max_transaction_amount = preapproval_object.scope.max_transaction_amount

    return models.FundsPullPreApprovalCommand(
        account_id=account_id,
        funds_pull_pre_approval_id=preapproval_object.funds_pull_pre_approval_id,
        address=preapproval_object.address,
        biller_address=preapproval_object.biller_address,
        funds_pull_pre_approval_type=preapproval_object.scope.type,
        expiration_timestamp=preapproval_object.scope.expiration_timestamp,
        max_cumulative_unit=max_cumulative_amount.unit
        if max_cumulative_amount
        else None,
        max_cumulative_unit_value=max_cumulative_amount.value
        if max_cumulative_amount
        else None,
        max_cumulative_amount=max_cumulative_amount.max_amount.amount
        if max_cumulative_amount
        else None,
        max_cumulative_amount_currency=max_cumulative_amount.max_amount.currency
        if max_cumulative_amount
        else None,
        max_transaction_amount=max_transaction_amount.amount
        if max_transaction_amount
        else None,
        max_transaction_amount_currency=max_transaction_amount.currency
        if max_transaction_amount
        else None,
        description=preapproval_object.description,
        status=preapproval_object.status,
        role=role,
    )


def validate_expiration_timestamp(expiration_timestamp):
    if expiration_timestamp < time.time():
        raise ValueError("expiration timestamp must be in the future")
