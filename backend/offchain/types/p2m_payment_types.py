import typing
from enum import Enum

import context
from .command_types import CommandType, ResponseType
from dataclasses import dataclass, field as datafield
from .p2p_payment_types import AddressObject, PaymentActionObject, NationalIdObject


@dataclass(frozen=True)
class GetPaymentInfo:
    reference_id: str
    _ObjectType: str = datafield(
        default=CommandType.GetPaymentInfo,
        metadata={"valid-values": [CommandType.GetPaymentInfo]},
    )


@dataclass(frozen=True)
class BusinessDataObject:
    name: str
    legal_name: str
    address: AddressObject


@dataclass(frozen=True)
class PaymentReceiverObject:
    address: str
    business_data: BusinessDataObject


@dataclass(frozen=True)
class PaymentInfoObject:
    receiver: PaymentReceiverObject
    action: PaymentActionObject
    reference_id: str
    description: str

    @staticmethod
    def new_payment_info_object(
        reference_id: str,
        receiver_address: str,
        name: str,
        legal_name: str,
        city: str,
        country: str,
        line1: str,
        line2: str,
        postal_code: str,
        state: str,
        amount: int,
        currency: str,
        action: str,
        timestamp: int,
        valid_until: typing.Optional[int] = None,
        description: typing.Optional[str] = None,
    ) -> "PaymentInfoObject":
        return PaymentInfoObject(
            receiver=PaymentReceiverObject(
                address=receiver_address,
                business_data=BusinessDataObject(
                    name=name,
                    legal_name=legal_name,
                    address=AddressObject.new_address_object(
                        city=city,
                        country=country,
                        line1=line1,
                        line2=line2,
                        postal_code=postal_code,
                        state=state,
                    ),
                ),
            ),
            action=PaymentActionObject(
                amount=amount,
                currency=currency,
                action=action,
                timestamp=timestamp,
                valid_until=valid_until,
            ),
            reference_id=reference_id,
            description=description,
        )


@dataclass(frozen=True)
class GetInfoCommandResponse:
    payment_info: PaymentInfoObject
    _ObjectType: str = datafield(default=ResponseType.GetInfoCommandResponse)


@dataclass(frozen=True)
class InitChargePaymentResponse:
    recipient_signature: typing.Optional[str] = None
    _ObjectType: str = datafield(default=ResponseType.InitChargePaymentResponse)


@dataclass(frozen=True)
class PayerDataObject:
    given_name: str
    surname: str
    address: AddressObject
    national_id: NationalIdObject

    @staticmethod
    def new_payer_data_object(
        city,
        country,
        line1,
        line2,
        my_name,
        my_sure_name,
        national_id_type,
        national_id_value,
        postal_code,
        state,
    ) -> "PayerDataObject":
        return PayerDataObject(
            given_name=my_name,
            surname=my_sure_name,
            address=AddressObject.new_address_object(
                city=city,
                country=country,
                line1=line1,
                line2=line2,
                postal_code=postal_code,
                state=state,
            ),
            national_id=NationalIdObject.new_national_id_object(
                country, national_id_type, national_id_value
            ),
        )


@dataclass(frozen=True)
class PaymentSenderObject:
    account_address: str
    payer_data: PayerDataObject

    @staticmethod
    def new_payment_sender_object(
        city,
        country,
        line1,
        line2,
        my_name,
        my_sure_name,
        national_id_type,
        national_id_value,
        postal_code,
        state,
    ) -> "PaymentSenderObject":
        return PaymentSenderObject(
            account_address=context.get().config.vasp_account_address().to_hex(),
            payer_data=PayerDataObject.new_payer_data_object(
                city,
                country,
                line1,
                line2,
                my_name,
                my_sure_name,
                national_id_type,
                national_id_value,
                postal_code,
                state,
            ),
        )


@dataclass(frozen=True)
class InitChargePayment:
    sender: PaymentSenderObject
    reference_id: str
    _ObjectType: str = datafield(default=CommandType.InitChargePayment)


@dataclass(frozen=True)
class InitAuthorizeCommand:
    sender: PaymentSenderObject
    reference_id: str
    _ObjectType: str = datafield(default=CommandType.InitAuthorizeCommand)


class P2MAbortCode(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CUSTOMER_DECLINED = "customer_declined"
    BUSINESS_NOT_VERIFIED = "business_not_verified"
    MISSING_RECIPIENT_SIGNATURE = "missing_recipient_signature"
    COULD_NOT_PUT_TRANSACTION = "could_not_put_transaction"
    UNSPECIFIED_ERROR = "unspecified_error"


@dataclass(frozen=True)
class AbortPayment:
    reference_id: str
    abort_code: typing.Optional[str] = None
    abort_message: typing.Optional[str] = None
    _ObjectType: str = datafield(default=CommandType.AbortPayment)
