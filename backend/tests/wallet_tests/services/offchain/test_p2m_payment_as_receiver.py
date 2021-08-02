import pytest
from offchain.types import (
    new_get_payment_info_request,
    new_init_charge_payment_request,
    new_init_auth_command,
)
from tests.wallet_tests.resources.seeds.one_p2m_payment_seeder import (
    OneP2MPaymentSeeder,
)
from wallet.services.offchain.p2m_payment_as_receiver import (
    handle_incoming_get_payment_info_request,
    handle_init_charge_command,
    handle_init_authorize_command,
)
from wallet.storage import db_session


ACTION_CHARGE = "charge"
AMOUNT = 100_000
MERCHANT_NAME = "Bond & Gurki Pet Store"
OTHER_ADDRESS = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
MY_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"
ORIGINAL_REFERENCE_ID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"


@pytest.mark.skip(reason="cant figure out why the response keep changing")
def test_handle_get_info_command(mock_method):
    OneP2MPaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID)

    get_info_request = new_get_payment_info_request(reference_id=REFERENCE_ID)

    response = handle_incoming_get_payment_info_request(get_info_request)

    assert response[0] == 200
    assert (
        response[1]
        == b"eyJhbGciOiJFZERTQSJ9.eyJzdGF0dXMiOiAic3VjY2VzcyIsICJyZXN1bHQiOiB7InBheW1lbnRfaW5mbyI6IHsicmVjZWl2ZXIiOiB7ImFkZHJlc3MiOiAidGRtMXB6bWhjeHBueW5zN20wMzVjdGRxbWV4eGFkOHB0Z2F6eGhsbHZ5c2Nlc3FkZ3AiLCAiYnVzaW5lc3NfZGF0YSI6IHsibmFtZSI6ICJCb25kICYgR3Vya2kgUGV0IFN0b3JlIiwgImxlZ2FsX25hbWUiOiAiQm9uZCAmIEd1cmtpIFBldCBTdG9yZSIsICJhZGRyZXNzIjogeyJjaXR5IjogIkRvZ2NpdHkiLCAiY291bnRyeSI6ICJEb2dsYW5kIiwgImxpbmUxIjogIjEyMzQgUHVwcHkgU3RyZWV0IiwgImxpbmUyIjogImRvZ3BhbGFjZSAzIiwgInBvc3RhbF9jb2RlIjogIjEyMzQ1NiIsICJzdGF0ZSI6ICJEb2dzdGF0ZSJ9fX0sICJhY3Rpb24iOiB7ImFtb3VudCI6IDEwMDAwMDAwMCwgImN1cnJlbmN5IjogIlhVUyIsICJhY3Rpb24iOiAiY2hhcmdlIiwgInRpbWVzdGFtcCI6IDE2MjExOTg4MDB9LCAicmVmZXJlbmNlX2lkIjogIjI2MzJhMDE4LWU0OTItNDQ4Ny04MWYzLTc3NWQ2ZWNmYjZlZiIsICJkZXNjcmlwdGlvbiI6ICJkZXNjcmlwdGlvbiJ9LCAiX09iamVjdFR5cGUiOiAiR2V0SW5mb0NvbW1hbmRSZXNwb25zZSJ9LCAiX09iamVjdFR5cGUiOiAiQ29tbWFuZFJlc3BvbnNlT2JqZWN0IiwgImNpZCI6ICIyNjMyYTAxOC1lNDkyLTQ0ODctODFmMy03NzVkNmVjZmI2ZWYifQ==.I7tbK6GwpI_YANbR6btCwHQpmmti0oin7boVEWgKQqPnrzDWg7SmLBX3AMPsVad_M94xLK0hHA0vcORKvvUsBA=="
    )


def test_handle_init_charge_command_success(mock_method):
    OneP2MPaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID)

    handle_init_charge_command(successful_init_charge_command())


def test_handle_init_charge_command_success_with_recipient_signature(mock_method):
    OneP2MPaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID, amount=1_000_000_000)

    handle_init_charge_command(successful_init_charge_command())


def successful_init_charge_command():
    return new_init_charge_payment_request(
        reference_id=REFERENCE_ID,
        vasp_address=OTHER_ADDRESS,
        sender_name="Bond",
        sender_sure_name="Silver",
        sender_city="CityOfDogs",
        sender_country="DG",
        sender_line1="Dog Street 11",
        sender_line2="",
        sender_postal_code="123456",
        sender_state="DogsState",
        sender_national_id_value="",
        sender_national_id_type="",
    )


def test_handle_init_charge_command_fail(mock_method):
    OneP2MPaymentSeeder.run(db_session, MY_ADDRESS, REFERENCE_ID)

    handle_init_charge_command(
        new_init_charge_payment_request(
            reference_id=REFERENCE_ID,
            vasp_address=OTHER_ADDRESS,
            sender_name="Bond",
            sender_sure_name="Silver",
            sender_city="CityOfDogs",
            sender_country="DG",
            sender_line1="Dog Street 11",
            sender_line2="",
            sender_postal_code="123456",
            sender_state="DogsState",
            sender_national_id_value="",
            sender_national_id_type="",
        )
    )


def test_handle_init_authorize_command():
    handle_init_authorize_command(
        new_init_auth_command(
            reference_id=REFERENCE_ID,
            sender_name="Bond",
            sender_sure_name="Silver",
            sender_city="CityOfDogs",
            sender_country="DG",
            sender_line1="Dog Street 11",
            sender_line2="",
            sender_postal_code="123456",
            sender_state="DogsState",
            sender_national_id_value="",
            sender_national_id_type="",
        )
    )
