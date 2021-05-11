import dataclasses
import logging
import typing
from datetime import datetime

from diem_utils.types.currencies import DiemCurrency
from offchain import (
    GetInfoCommandObject,
    CommandRequestObject,
    jws,
)
from offchain.types import (
    new_payment_info_object,
    new_get_info_request,
    GetInfoCommandResponse,
    new_init_charge_command,
    new_init_auth_command,
    InitChargeCommandResponse,
    InitChargeCommand,
    InitAuthorizeCommand,
)
from wallet import storage
from wallet.services.offchain import utils
from wallet.services.offchain.utils import generate_my_address
from wallet.storage.models import Payment as PaymentModel
from wallet.storage.payment import save_payment
from wallet.types import TransactionType, TransactionStatus

logger = logging.getLogger(__name__)


def handle_get_info_command(request: CommandRequestObject):
    # The get_info command arrive only when LRW playing the Merchant\Receiver role in the communication,
    # and therefore we can assume that the payment info already been saved in DB
    # and the missing data we can mock
    get_info_command_object = typing.cast(GetInfoCommandObject, request.command)

    reference_id = get_info_command_object.reference_id

    payment_model = storage.get_payment_details(reference_id)

    payment_info_object = new_payment_info_object(
        reference_id=reference_id,
        receiver_address=payment_model.vasp_address,
        name=payment_model.merchant_name,
        legal_name=payment_model.merchant_name,
        city="Dogcity",
        country="Dogland",
        line1="1234 Puppy Street",
        line2="dogpalace",
        postal_code="123456",
        state="Dogstate",
        amount=payment_model.amount,
        currency=payment_model.currency,
        action=payment_model.action,
        timestamp=int(datetime.timestamp(payment_model.created_at)),
        valid_until=int(datetime.timestamp(payment_model.expiration))
        if payment_model.action == "auth"
        else None,
        description=payment_model.description,
    )

    return utils.jws_response(
        reference_id,
        result_object=GetInfoCommandResponse(payment_info=payment_info_object),
    )


def handle_init_charge_command(request: CommandRequestObject):
    init_charge_command_object = typing.cast(InitChargeCommand, request.command)

    reference_id = init_charge_command_object.reference_id

    # TODO
    recipient_signature = ""

    return utils.jws_response(
        reference_id,
        result_object=InitChargeCommandResponse(
            recipient_signature=recipient_signature
        ),
    )


def handle_init_authorize_command(request: CommandRequestObject):
    init_auth_command_object = typing.cast(InitAuthorizeCommand, request.command)

    reference_id = init_auth_command_object.reference_id

    payment_model = storage.get_payment_details(reference_id)

    return utils.jws_response(reference_id)


@dataclasses.dataclass(frozen=True)
class PaymentDetails:
    vasp_address: str
    reference_id: str
    merchant_name: str
    action: str
    currency: str
    amount: int
    expiration: int


class P2MGeneralError(Exception):
    pass


def get_payment_details(account_id, reference_id: str, vasp_address: str):
    payment_model = storage.get_payment_details(reference_id)

    if payment_model is None:
        my_address = utils.generate_my_address(account_id)

        try:
            command_response_object = utils.offchain_client().send_request(
                request_sender_address=my_address,
                counterparty_account_id=vasp_address,
                request_bytes=jws.serialize(
                    new_get_info_request(reference_id=reference_id, cid=reference_id),
                    utils.compliance_private_key().sign,
                ),
            )
        except Exception as e:
            error = P2MGeneralError(e)
            logger.error(error)
            raise error

        if (
            command_response_object.result
            and type(command_response_object.result) is GetInfoCommandResponse
        ):
            payment_info = command_response_object.result.payment_info
            action_object = payment_info.action

            payment_model = save_payment(
                PaymentModel(
                    vasp_address=vasp_address,
                    my_address=my_address,
                    reference_id=reference_id,
                    merchant_name=payment_info.receiver.business_data.name,
                    action=action_object.action,
                    currency=action_object.currency,
                    amount=action_object.amount,
                    expiration=datetime.fromtimestamp(action_object.valid_until)
                    if action_object.valid_until
                    else None,
                )
            )

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
    )

    save_payment(payment_command)


def approve_payment(account_id, reference_id):
    payment_model = storage.get_payment_details(reference_id)

    if not payment_model:
        raise P2MGeneralError(f"Could not find payment {reference_id}")

    if payment_model.action == "charge":
        user = storage.get_user(account_id)

        try:
            command_response_object = utils.offchain_client().send_request(
                request_sender_address=payment_model.my_address,
                counterparty_account_id=payment_model.vasp_address,
                request_bytes=jws.serialize(
                    new_init_charge_command(
                        reference_id=payment_model.reference_id,
                        vasp_address=payment_model.vasp_address,
                        my_name=user.first_name,
                        my_sure_name=user.last_name,
                        city=user.city,
                        country=user.country,
                        line1=user.address_1,
                        line2=user.address_2,
                        postal_code=user.zip,
                        state=user.state,
                        national_id_value="",
                        national_id_type="",
                    ),
                    utils.compliance_private_key().sign,
                ),
            )

            if (
                command_response_object.result
                and type(command_response_object.result) is InitChargeCommandResponse
            ):
                recipient_signature = command_response_object.result.recipient_signature

                storage.update_payment(reference_id, recipient_signature)
        except Exception as e:
            error = P2MGeneralError(e)
            logger.error(error)
            raise error
    elif payment_model.action == "auth":
        user = storage.get_user(account_id)

        try:
            utils.offchain_client().send_request(
                request_sender_address=payment_model.my_address,
                counterparty_account_id=payment_model.vasp_address,
                request_bytes=jws.serialize(
                    new_init_auth_command(
                        reference_id=payment_model.reference_id,
                        vasp_address=payment_model.vasp_address,
                        my_name=user.first_name,
                        my_sure_name=user.last_name,
                        city=user.city,
                        country=user.country,
                        line1=user.address_1,
                        line2=user.address_2,
                        postal_code=user.zip,
                        state=user.state,
                        national_id_value="",
                        national_id_type="",
                    ),
                    utils.compliance_private_key().sign,
                ),
            )

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
        except Exception as e:
            error = P2MGeneralError(e)
            logger.error(error)
            raise error
    else:
        raise P2MGeneralError(f"Unsupported action type {payment_model.action}")
