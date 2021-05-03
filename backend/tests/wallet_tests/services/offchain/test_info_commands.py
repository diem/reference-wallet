import time

import context
from diem_utils.types.currencies import DiemCurrency
from offchain import (
    CommandResponseObject,
    PaymentActionObject,
    AddressObject,
    OffChainErrorObject,
)
from offchain.types import GetInfoCommandResponse, PaymentInfoObject
from offchain.types.info_types import PaymentReceiverObject, BusinessDataObject
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services.offchain import info_commands as info_commands_service
from wallet.storage import db_session

CREATED_AT = int(time.time())
EXPIRATION = CREATED_AT + 3000

ACTION_CHARGE = "charge"
AMOUNT = 100_000
MERCHANT_NAME = "Bond & Gurki Pet Store"
OTHER_ADDRESS = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
MY_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"
ORIGINAL_REFERENCE_ID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"


def test_get_payment_info_for_charge_action_successfully(mock_method):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    mock_method(
        context.get().offchain_client,
        "send_request",
        will_return=generate_success_command_response_object(),
    )

    payment_info = info_commands_service.get_payment_info(
        user.account_id, REFERENCE_ID, OTHER_ADDRESS
    )

    assert payment_info.action == ACTION_CHARGE
    assert payment_info.amount == AMOUNT
    assert payment_info.currency == DiemCurrency.XUS
    assert payment_info.merchant_name == MERCHANT_NAME
    assert payment_info.reference_id == REFERENCE_ID
    assert payment_info.vasp_address == OTHER_ADDRESS


def test_get_payment_info_for_charge_action_failure(mock_method):
    # TODO
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    mock_method(
        context.get().offchain_client,
        "send_request",
        will_return=generate_failed_command_response_object(),
    )

    payment_info = info_commands_service.get_payment_info(
        user.account_id, REFERENCE_ID, OTHER_ADDRESS
    )

    assert payment_info is None


def generate_failed_command_response_object():
    return CommandResponseObject(
        status="failure",
        error=OffChainErrorObject(type="command_error", code=123, field="", message=""),
        cid=REFERENCE_ID,
    )


def generate_success_command_response_object():
    return CommandResponseObject(
        status="success",
        result=GetInfoCommandResponse(
            _ObjectType="GetInfoCommandResponse",
            payment_info=PaymentInfoObject(
                receiver=PaymentReceiverObject(
                    address=OTHER_ADDRESS,
                    business_data=BusinessDataObject(
                        name=MERCHANT_NAME,
                        legal_name=MERCHANT_NAME,
                        address=AddressObject(
                            city="CityOfDogs",
                            country="DogsCountry",
                            line1="Dog Street 11",
                            line2="",
                            postal_code="123456",
                            state="DogsState",
                        ),
                    ),
                ),
                action=PaymentActionObject(
                    amount=AMOUNT,
                    currency=DiemCurrency.XUS,
                    action=ACTION_CHARGE,
                    timestamp=CREATED_AT,
                ),
                reference_id=REFERENCE_ID,
                description="bla bla bla",
            ),
        ),
        cid=REFERENCE_ID,
    )


# def test_get_none_payment_details():
#     user = OneUser.run(
#         db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
#     )
#
#     payment_info = info_commands_service.get_payment_info(
#         user.account_id, REFERENCE_ID, OTHER_ADDRESS
#     )
#
#     assert payment_info is None
