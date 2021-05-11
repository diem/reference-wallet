import logging
from datetime import datetime

import context
import pytest
from diem_utils.types.currencies import DiemCurrency
from offchain import (
    CommandResponseObject,
    PaymentActionObject,
    AddressObject,
    OffChainErrorObject,
    CommandResponseError,
)
from offchain.types import (
    GetInfoCommandResponse,
    PaymentInfoObject,
    new_get_info_request,
)
from offchain.types.payment_types import (
    PaymentReceiverObject,
    BusinessDataObject,
    InitChargeCommandResponse,
)
from tests.wallet_tests.resources.seeds.one_payment_seeder import OnePaymentSeeder
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet import storage
from wallet.services.offchain import payment as info_commands_service
from wallet.services.offchain import payment as payment_service
from wallet.storage import db_session

CREATED_AT = datetime(2021, 5, 12)
EXPIRATION = datetime(2021, 5, 17)

ACTION_CHARGE = "charge"
AMOUNT = 100_000
MERCHANT_NAME = "Bond & Gurki Pet Store"
OTHER_ADDRESS = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
MY_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"
ORIGINAL_REFERENCE_ID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"


def test_get_payment_details_for_charge_action_successfully(mock_method):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    mock_method(
        context.get().offchain_client,
        "send_request",
        will_return=generate_success_get_info_command_response_object(),
    )

    payment_info = info_commands_service.get_payment_details(
        user.account_id, REFERENCE_ID, OTHER_ADDRESS
    )

    assert payment_info.action == ACTION_CHARGE
    assert payment_info.amount == AMOUNT
    assert payment_info.currency == DiemCurrency.XUS
    assert payment_info.merchant_name == MERCHANT_NAME
    assert payment_info.reference_id == REFERENCE_ID
    assert payment_info.vasp_address == OTHER_ADDRESS


def test_get_payment_details_for_charge_action_failure(mock_method):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    mock_method(
        context.get().offchain_client,
        "send_request",
        will_raise=CommandResponseError(generate_failed_command_response_object()),
    )

    with pytest.raises(payment_service.P2MGeneralError):
        info_commands_service.get_payment_details(
            user.account_id, REFERENCE_ID, OTHER_ADDRESS
        )


def generate_failed_command_response_object():
    return CommandResponseObject(
        status="failure",
        error=OffChainErrorObject(type="command_error", code=123, field="", message=""),
        cid=REFERENCE_ID,
    )


def generate_success_get_info_command_response_object():
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


def test_handle_get_info_command(mock_method):
    OnePaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID)

    get_info_request = new_get_info_request(reference_id=REFERENCE_ID, cid=REFERENCE_ID)

    response = info_commands_service.handle_get_info_command(get_info_request)

    assert response[0] == 200
    assert (
        response[1]
        == b"eyJhbGciOiJFZERTQSJ9.eyJzdGF0dXMiOiAic3VjY2VzcyIsICJyZXN1bHQiOiB7InBheW1lbnRfaW5mbyI6IHsicmVjZWl2ZXIiOiB7ImFkZHJlc3MiOiAidGRtMXB6bWhjeHBueW5zN20wMzVjdGRxbWV4eGFkOHB0Z2F6eGhsbHZ5c2Nlc3FkZ3AiLCAiYnVzaW5lc3NfZGF0YSI6IHsibmFtZSI6ICJCb25kICYgR3Vya2kgUGV0IFN0b3JlIiwgImxlZ2FsX25hbWUiOiAiQm9uZCAmIEd1cmtpIFBldCBTdG9yZSIsICJhZGRyZXNzIjogeyJjaXR5IjogIkRvZ2NpdHkiLCAiY291bnRyeSI6ICJEb2dsYW5kIiwgImxpbmUxIjogIjEyMzQgUHVwcHkgU3RyZWV0IiwgImxpbmUyIjogImRvZ3BhbGFjZSAzIiwgInBvc3RhbF9jb2RlIjogIjEyMzQ1NiIsICJzdGF0ZSI6ICJEb2dzdGF0ZSJ9fX0sICJhY3Rpb24iOiB7ImFtb3VudCI6IDEwMDAwMDAwMCwgImN1cnJlbmN5IjogIlhVUyIsICJhY3Rpb24iOiAiY2hhcmdlIiwgInRpbWVzdGFtcCI6IDE2MjExOTg4MDB9LCAicmVmZXJlbmNlX2lkIjogIjI2MzJhMDE4LWU0OTItNDQ4Ny04MWYzLTc3NWQ2ZWNmYjZlZiIsICJkZXNjcmlwdGlvbiI6ICJkZXNjcmlwdGlvbiJ9LCAiX09iamVjdFR5cGUiOiAiR2V0SW5mb0NvbW1hbmRSZXNwb25zZSJ9LCAiX09iamVjdFR5cGUiOiAiQ29tbWFuZFJlc3BvbnNlT2JqZWN0IiwgImNpZCI6ICIyNjMyYTAxOC1lNDkyLTQ0ODctODFmMy03NzVkNmVjZmI2ZWYifQ==.I7tbK6GwpI_YANbR6btCwHQpmmti0oin7boVEWgKQqPnrzDWg7SmLBX3AMPsVad_M94xLK0hHA0vcORKvvUsBA=="
    )


def test_add_new_payment():
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    expiration = 1802010490

    payment_service.add_new_payment(
        account_id=user.account_id,
        reference_id=REFERENCE_ID,
        vasp_address=OTHER_ADDRESS,
        merchant_name=MERCHANT_NAME,
        action=ACTION_CHARGE,
        currency=DiemCurrency.XUS,
        amount=AMOUNT,
        expiration=expiration,
    )

    payment_details = storage.get_payment_details(REFERENCE_ID)

    assert payment_details
    assert payment_details.reference_id == REFERENCE_ID
    assert payment_details.vasp_address == OTHER_ADDRESS
    assert payment_details.merchant_name == MERCHANT_NAME
    assert payment_details.action == ACTION_CHARGE
    assert payment_details.currency == DiemCurrency.XUS
    assert payment_details.amount == AMOUNT
    assert int(datetime.timestamp(payment_details.expiration)) == expiration


def generate_success_init_charge_command_response_object():
    return CommandResponseObject(
        status="success",
        result=InitChargeCommandResponse(
            _ObjectType="GetInfoCommandResponse",
            recipient_signature=b"I have no idea what to write here",
        ),
        cid=REFERENCE_ID,
    )


def test_approve_payment_success(mock_method):
    """
    since we mock the offchain send_request all we left to verify is
    if the payment record in DB are update correctly if any update required
    """
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    OnePaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID)

    mock_method(
        context.get().offchain_client,
        "send_request",
        will_return=generate_success_init_charge_command_response_object(),
    )

    payment_service.approve_payment(user.account_id, REFERENCE_ID)

    payment_model = storage.get_payment_details(REFERENCE_ID)

    assert payment_model.recipient_signature


def test_approve_payment_fail_because_payment_not_exist():
    with pytest.raises(payment_service.P2MGeneralError):
        payment_service.approve_payment(1, REFERENCE_ID)


def test_approve_payment_unsupported_action_type():
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    OnePaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID, action="dog")

    with pytest.raises(payment_service.P2MGeneralError):
        payment_service.approve_payment(user.account_id, REFERENCE_ID)
