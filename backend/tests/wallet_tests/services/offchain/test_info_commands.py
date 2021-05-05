import time

import context
from diem_utils.types.currencies import DiemCurrency
from offchain import (
    CommandResponseObject,
    PaymentActionObject,
    AddressObject,
    OffChainErrorObject,
)
from offchain.types import (
    GetInfoCommandResponse,
    PaymentInfoObject,
    new_get_info_request,
)
from offchain.types.info_types import PaymentReceiverObject, BusinessDataObject
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services.offchain import info_command as info_commands_service, utils
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


def test_handle_get_info_command(mock_method):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    # mocking generate_my_address to insure my_address consistency
    mock_method(utils, "generate_my_address", will_return=MY_ADDRESS)

    response = info_commands_service.handle_get_info_command(
        new_get_info_request(reference_id=REFERENCE_ID, cid=REFERENCE_ID),
        user.account_id,
    )

    assert response[0] == 200
    assert (
        response[1]
        == b"eyJhbGciOiJFZERTQSJ9.eyJzdGF0dXMiOiAic3VjY2VzcyIsICJyZXN1bHQiOiB7InJlY2VpdmVyIjogeyJhZGRyZXNzIjogInRkbTFwem1oY3hwbnluczdtMDM1Y3RkcW1leHhhZDhwdGdhenhobGx2eXNjZXNxZGdwIiwgImJ1c2luZXNzX2RhdGEiOiB7Im5hbWUiOiAiQm9uZCAmIEd1cmtpIFBldCBTdG9yZSIsICJsZWdhbF9uYW1lIjogIkJvbmQgJiBHdXJraSBQZXQgU3RvcmUiLCAiYWRkcmVzcyI6IHsiY2l0eSI6ICJEb2djaXR5IiwgImNvdW50cnkiOiAiRG9nbGFuZCIsICJsaW5lMSI6ICIxMjM0IFB1cHB5IFN0cmVldCIsICJsaW5lMiI6ICJkb2dwYWxhY2UgMyIsICJwb3N0YWxfY29kZSI6ICIxMjM0NTYiLCAic3RhdGUiOiAiRG9nc3RhdGUifX19LCAiYWN0aW9uIjogeyJhbW91bnQiOiAxMDAwMDAwMDAsICJjdXJyZW5jeSI6ICJYVVMiLCAiYWN0aW9uIjogImNoYXJnZSIsICJ0aW1lc3RhbXAiOiAxMjN9LCAicmVmZXJlbmNlX2lkIjogIjI2MzJhMDE4LWU0OTItNDQ4Ny04MWYzLTc3NWQ2ZWNmYjZlZiIsICJkZXNjcmlwdGlvbiI6ICJkZXNjcmlwdGlvbiJ9LCAiX09iamVjdFR5cGUiOiAiQ29tbWFuZFJlc3BvbnNlT2JqZWN0IiwgImNpZCI6ICIyNjMyYTAxOC1lNDkyLTQ0ODctODFmMy03NzVkNmVjZmI2ZWYifQ==.P1C2b6SWCSR2j10IG-gN3wVIqxKdGQah-7uRnv2Vg8-NGkGfIUDXe4K_uVkwOyxQa2n_EYeX1FlEVdhSQ_JRCQ=="
    )
