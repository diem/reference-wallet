import dataclasses
import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from diem_utils.types.currencies import DiemCurrency
from offchain import (
    jws,
)
from offchain.types import (
    new_get_payment_info_request,
    new_init_charge_payment_request,
    new_init_auth_command,
    InitChargePaymentResponse,
    new_abort_payment_command,
    P2MAbortCode,
)
from wallet import storage
from wallet.services import transaction
from wallet.services.offchain import utils
from wallet.services.offchain.utils import generate_my_address
from wallet.storage.models import Payment as PaymentModel
from wallet.storage.p2m_payment import save_payment
from wallet.types import TransactionType, TransactionStatus

logger = logging.getLogger(__name__)


class P2MPaymentStatus(str, Enum):
    READY_FOR_USER = "ready_for_user"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclasses.dataclass(frozen=True)
class PaymentDetails:
    vasp_address: str
    reference_id: str
    merchant_name: str
    action: str
    currency: str
    amount: int
    expiration: int
    status: P2MPaymentStatus
    demo: bool = False


class P2MGeneralError(Exception):
    pass


class P2MPaymentNotFoundError(Exception):
    pass


def get_payment_details(account_id: int, reference_id: str, receiver_address: str):
    payment_model = storage.get_payment_details(reference_id)

    if payment_model is None:
        my_address = utils.generate_my_address(account_id)

        try:
            command_response_object = utils.offchain_client().send_request(
                request_sender_address=my_address,
                counterparty_account_id=receiver_address,
                request_bytes=jws.serialize(
                    new_get_payment_info_request(reference_id=reference_id),
                    utils.compliance_private_key().sign,
                ),
            )

            payment_info = command_response_object.result.payment_info
            action_object = payment_info.action

            payment_model = save_payment(
                PaymentModel(
                    vasp_address=receiver_address,
                    my_address=my_address,
                    reference_id=reference_id,
                    merchant_name=payment_info.receiver.business_data.name,
                    action=action_object.action,
                    currency=action_object.currency,
                    amount=action_object.amount,
                    expiration=datetime.fromtimestamp(action_object.valid_until)
                    if action_object.valid_until
                    else None,
                    status=P2MPaymentStatus.READY_FOR_USER,
                )
            )
        except Exception as e:
            error = P2MGeneralError(e)
            logger.error(error)
            raise error
    return PaymentDetails(
        vasp_address=payment_model.vasp_address,
        reference_id=payment_model.reference_id,
        merchant_name=payment_model.merchant_name,
        action=payment_model.action,
        currency=payment_model.currency,
        amount=payment_model.amount,
        expiration=int(datetime.timestamp(payment_model.expiration))
        if payment_model.expiration
        else None,
        status=payment_model.status,
    )


def add_new_payment(
    account_id,
    reference_id,
    vasp_address,
    merchant_name,
    action,
    currency,
    amount,
    expiration,
    demo: bool = False,
):
    payment_command = PaymentModel(
        vasp_address=vasp_address,
        my_address=generate_my_address(account_id),
        reference_id=reference_id,
        merchant_name=merchant_name,
        action=action,
        currency=currency,
        amount=amount,
        expiration=datetime.fromtimestamp(expiration) if expiration else None,
        status=P2MPaymentStatus.READY_FOR_USER,
    )

    save_payment(payment_command)


def approve_payment(
    account_id: int, reference_id: str, init_required: Optional[bool] = True
):
    payment_model = storage.get_payment_details(reference_id)

    if not payment_model:
        raise P2MPaymentNotFoundError(f"Could not find payment {reference_id}")

    if payment_model.action == "charge":
        if init_required:
            (
                payment_model,
                account_id,
                recipient_signature,
            ) = send_init_charge_payment_request(payment_model, account_id)
            transaction.submit_p2m_transaction(
                payment_model, account_id, recipient_signature
            )
    elif payment_model.action == "auth":
        if init_required:
            send_init_auth_payment_request(payment_model, account_id)

        lock_funds(account_id, payment_model, reference_id)
    else:
        raise P2MGeneralError(f"Unsupported action type {payment_model.action}")


def reject_payment(reference_id: str):
    payment_model = storage.get_payment_details(reference_id)

    if not payment_model:
        raise P2MPaymentNotFoundError(f"Could not find payment {reference_id}")

    try:
        command_response_object = utils.offchain_client().send_request(
            request_sender_address=payment_model.my_address,
            counterparty_account_id=payment_model.vasp_address,
            request_bytes=jws.serialize(
                new_abort_payment_command(
                    reference_id=payment_model.reference_id,
                    abort_message="customer rejected payment request",
                    abort_code=P2MAbortCode.CUSTOMER_DECLINED,
                ),
                utils.compliance_private_key().sign,
            ),
        )

        if command_response_object:
            if command_response_object.status == "success":
                storage.update_payment(
                    reference_id=payment_model.reference_id,
                    status=P2MPaymentStatus.REJECTED,
                )
            else:
                # todo throw?
                ...
    except Exception as e:
        error = P2MGeneralError(e)
        logger.error(error)
        raise error


def lock_funds(account_id, payment_model, reference_id):
    my_address, my_sub_address = utils.account_address_and_subaddress(
        payment_model.my_address
    )
    vasp_address, vasp_sub_address = utils.account_address_and_subaddress(
        payment_model.vasp_address
    )
    storage.add_transaction(
        amount=payment_model.amount,
        currency=DiemCurrency[payment_model.currency],
        payment_type=TransactionType.EXTERNAL,
        status=TransactionStatus.LOCKED,
        source_id=account_id,
        source_address=my_address,
        source_subaddress=my_sub_address,
        destination_id=None,
        destination_address=vasp_address,
        destination_subaddress=vasp_sub_address,
        reference_id=reference_id,
    )


def send_init_auth_payment_request(payment_model, account_id):
    user = storage.get_user(account_id)

    try:
        utils.offchain_client().send_request(
            request_sender_address=payment_model.my_address,
            counterparty_account_id=payment_model.vasp_address,
            request_bytes=jws.serialize(
                new_init_auth_command(
                    reference_id=payment_model.reference_id,
                    sender_name=user.first_name,
                    sender_sure_name=user.last_name,
                    sender_city=user.city,
                    sender_country=user.country,
                    sender_line1=user.address_1,
                    sender_line2=user.address_2,
                    sender_postal_code=user.zip,
                    sender_state=user.state,
                    sender_national_id_value="000000000",
                    sender_national_id_type="",
                ),
                utils.compliance_private_key().sign,
            ),
        )
    except Exception as e:
        error = P2MGeneralError(e)
        logger.error(error)
        raise error


def send_init_charge_payment_request(payment_model, account_id):
    user = storage.get_user(account_id)

    try:
        command_response_object = utils.offchain_client().send_request(
            request_sender_address=payment_model.my_address,
            counterparty_account_id=payment_model.vasp_address,
            request_bytes=jws.serialize(
                new_init_charge_payment_request(
                    reference_id=payment_model.reference_id,
                    vasp_address=payment_model.vasp_address,
                    sender_name=user.first_name,
                    sender_sure_name=user.last_name,
                    sender_city=user.city,
                    sender_country=user.country,
                    sender_line1=user.address_1,
                    sender_line2=user.address_2,
                    sender_postal_code=user.zip,
                    sender_state=user.state,
                    sender_national_id_value="000000000",
                    sender_national_id_type="",
                ),
                utils.compliance_private_key().sign,
            ),
        )

        recipient_signature = None

        if (
            payment_model.amount >= 1_000_000_000
            and command_response_object.result
            and type(command_response_object.result) is InitChargePaymentResponse
        ):
            recipient_signature = command_response_object.result.recipient_signature

        storage.update_payment(
            reference_id=payment_model.reference_id,
            recipient_signature=recipient_signature,
            status=P2MPaymentStatus.APPROVED,
        )

        # todo verify response status?

        return payment_model, account_id, recipient_signature

    except Exception as e:
        error = P2MGeneralError(e)
        logger.error(error)
        raise error
