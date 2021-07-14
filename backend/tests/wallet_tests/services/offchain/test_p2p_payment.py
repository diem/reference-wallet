import context
from diem import identifier
from offchain import Status, AddressObject
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from tests.wallet_tests.resources.seeds.one_p2p_payment_seeder import (
    OneP2PPaymentSeeder,
)
from wallet.services.offchain import p2p_payment as pc_service
from wallet.storage import db_session, TransactionStatus
from wallet import storage
from wallet.storage.models import PaymentCommand as PaymentCommandModel
from datetime import datetime
import offchain
import time

CREATED_AT = int(time.time())
EXPIRATION = CREATED_AT + 3000


ACTION_CHARGE = "charge"
AMOUNT = 100_000
MERCHANT_NAME = "Bond & Gurki Pet Store"
OTHER_ADDRESS = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
MY_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"
ORIGINAL_REFERENCE_ID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"


def test_model_to_payment_command():
    model = PaymentCommandModel(
        reference_id=REFERENCE_ID,
        status=TransactionStatus.OFF_CHAIN_INBOUND,
        account_id=1,
        my_actor_address=MY_ADDRESS,
        inbound=True,
        cid=REFERENCE_ID,
        sender_address=MY_ADDRESS,
        sender_status=Status.needs_kyc_data,
        sender_kyc_data='{"type": "individual", "payload_version": 1, "given_name": "hello", "surname": "world", "address": {"city": "San Francisco", "country": "", "line1": "", "line2": "", "postal_code": "", "state": ""}, "dob": "1991-06-01", "place_of_birth": {"city": "San Francisco", "country": "", "line1": "", "line2": "", "postal_code": "", "state": ""}, "national_id": {"id_value": "234121234", "country": "", "type": ""}, "legal_entity_name": "foo bar"}',
        sender_metadata=["bond", "gurki"],
        sender_additional_kyc_data="sender_additional_kyc_data",
        receiver_address=OTHER_ADDRESS,
        receiver_status=Status.ready_for_settlement,
        receiver_kyc_data='{"type": "individual", "payload_version": 1, "given_name": "hello", "surname": "world", "address": {"city": "San Francisco", "country": "", "line1": "", "line2": "", "postal_code": "", "state": ""}, "dob": "1991-06-01", "place_of_birth": {"city": "San Francisco", "country": "", "line1": "", "line2": "", "postal_code": "", "state": ""}, "national_id": {"id_value": "234121234", "country": "", "type": ""}, "legal_entity_name": "foo bar"}',
        receiver_metadata='["bond", "gurki", b"dogs"]',
        receiver_additional_kyc_data="receiver_additional_kyc_data",
        amount=AMOUNT,
        currency=DiemCurrency.XUS,
        action="charge",
        created_at=datetime.fromtimestamp(CREATED_AT),
        original_payment_reference_id=ORIGINAL_REFERENCE_ID,
        recipient_signature="recipient_signature",
        description="description",
        merchant_name="merchant_name",
        expiration=datetime.fromtimestamp(EXPIRATION),
    )

    payment_command = pc_service.model_to_payment_command(model)

    check_conversion(model, payment_command)


def test_payment_command_to_model():
    payment_command = offchain.PaymentCommand(
        my_actor_address=MY_ADDRESS,
        inbound=True,
        cid=REFERENCE_ID,
        payment=offchain.PaymentObject(
            reference_id=REFERENCE_ID,
            sender=offchain.PaymentActorObject(
                address=MY_ADDRESS,
                status=offchain.StatusObject(status=Status.ready_for_settlement),
                kyc_data=offchain.KycDataObject(
                    type=offchain.KycDataObjectType.individual,
                    payload_version=1,
                    given_name="Bond",
                    surname="Marton",
                    address=AddressObject.new_address_object(
                        city="CityOfDogs",
                        country="DG",
                        line1="Dog Street 11",
                        line2="",
                        postal_code="123456",
                        state="DogsState",
                    ),
                    dob="2010-01-21",
                    place_of_birth=AddressObject.new_address_object(
                        city="CityOfPuppies",
                        country="PC",
                        line1="Puppy Street 1",
                        line2="",
                        postal_code="34567",
                        state="PuppiesState",
                    ),
                    national_id=offchain.NationalIdObject(
                        id_value="123-45-6789",
                        country="DG",
                        type="SSN",
                    ),
                    legal_entity_name="Prince Bond",
                ),
                metadata=["bond", "gurki"],
                additional_kyc_data="sender_additional_kyc_data",
            ),
            receiver=offchain.PaymentActorObject(
                address=OTHER_ADDRESS,
                status=offchain.StatusObject(status=Status.ready_for_settlement),
                kyc_data=offchain.KycDataObject(
                    type=offchain.KycDataObjectType.individual,
                    payload_version=1,
                    given_name="Gurki",
                    surname="Marton",
                    address=AddressObject.new_address_object(
                        city="CityOfDogs",
                        country="DG",
                        line1="Dog Street 11",
                        line2="",
                        postal_code="123456",
                        state="DogsState",
                    ),
                    dob="2011-11-11",
                    place_of_birth=AddressObject.new_address_object(
                        city="CityOfPuppies",
                        country="PC",
                        line1="Puppy Street 1",
                        line2="",
                        postal_code="34567",
                        state="PuppiesState",
                    ),
                    national_id=offchain.NationalIdObject(
                        id_value="123-45-6789",
                        country="DG",
                        type="SSN",
                    ),
                    legal_entity_name="Prince Bond",
                ),
                metadata=["bond", "gurki"],
                additional_kyc_data="receiver_additional_kyc_data",
            ),
            action=offchain.PaymentActionObject(
                amount=AMOUNT,
                currency=DiemCurrency.XUS,
                action="charge",
                timestamp=CREATED_AT,
                valid_until=EXPIRATION,
            ),
            original_payment_reference_id=ORIGINAL_REFERENCE_ID,
            recipient_signature="recipient_signature",
            description="description",
        ),
    )

    model = pc_service.payment_command_to_model(
        payment_command, TransactionStatus.PENDING
    )

    check_conversion(model, payment_command)


def check_conversion(model, payment_command):
    assert model.reference_id == payment_command.reference_id()
    assert model.my_actor_address == payment_command.my_actor_address
    assert model.inbound == payment_command.inbound
    assert model.cid == payment_command.cid
    assert model.sender_address == payment_command.payment.sender.address
    assert model.sender_status == payment_command.payment.sender.status.status
    assert model.sender_kyc_data == offchain.to_json(
        payment_command.payment.sender.kyc_data
    )
    assert model.sender_metadata == payment_command.payment.sender.metadata
    assert (
        model.sender_additional_kyc_data
        == payment_command.payment.sender.additional_kyc_data
    )
    assert model.receiver_address == payment_command.payment.receiver.address
    assert model.receiver_status == payment_command.payment.receiver.status.status
    assert model.receiver_kyc_data == offchain.to_json(
        payment_command.payment.receiver.kyc_data
    )
    assert model.receiver_metadata == payment_command.payment.receiver.metadata
    assert (
        model.receiver_additional_kyc_data
        == payment_command.payment.receiver.additional_kyc_data
    )
    assert model.amount == payment_command.payment.action.amount
    assert model.currency == payment_command.payment.action.currency
    assert model.action == payment_command.payment.action.action
    assert (
        model.original_payment_reference_id
        == payment_command.payment.original_payment_reference_id
    )
    assert model.recipient_signature == payment_command.payment.recipient_signature
    assert model.description == payment_command.payment.description
    assert (
        int(datetime.timestamp(model.created_at))
        == payment_command.payment.action.timestamp
    )
    assert (
        int(datetime.timestamp(model.expiration))
        == payment_command.payment.action.valid_until
    )


def test_add_payment_command():
    """
    Add payment command for outgoing 'charge' (immediately) payment.
    Check the offchain.PaymentCommand created base on add_payment_command
    call and the DB entry
    """
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    expiration = 1802010490

    pc_service.add_payment_command_as_sender(
        account_id=user.account_id,
        reference_id=REFERENCE_ID,
        vasp_address=OTHER_ADDRESS,
        merchant_name=MERCHANT_NAME,
        action=ACTION_CHARGE,
        currency=DiemCurrency.XUS,
        amount=AMOUNT,
        expiration=expiration,
    )

    check_payment_command()

    model = storage.get_payment_command(REFERENCE_ID)

    sender_address, _ = identifier.decode_account(
        model.sender_address, context.get().config.diem_address_hrp()
    )

    assert model
    assert model.reference_id == REFERENCE_ID
    assert model.merchant_name == MERCHANT_NAME
    assert model.expiration == datetime.fromtimestamp(expiration)
    assert sender_address.to_hex() == context.get().config.vasp_address
    assert model.sender_status == Status.none
    assert model.receiver_address == OTHER_ADDRESS
    assert model.receiver_status == Status.none
    assert model.amount == AMOUNT
    assert model.status == TransactionStatus.PENDING


def test_update_payment_command_status():
    """Update existing 'charge' payment to be 'ready_for_settlement' as payer"""
    sender_status = Status.none
    receiver_status = Status.none

    OneP2PPaymentSeeder.run(
        db_session,
        reference_id=REFERENCE_ID,
        amount=AMOUNT,
        sender_address=MY_ADDRESS,
        sender_status=sender_status,
        receiver_address=OTHER_ADDRESS,
        receiver_status=receiver_status,
        action=ACTION_CHARGE,
        is_sender=True,
        command_status=TransactionStatus.PENDING,
    )

    expected_my_actor_address, _ = identifier.decode_account(
        MY_ADDRESS, context.get().config.diem_address_hrp()
    )

    check_payment_command(expected_my_actor_address=expected_my_actor_address.to_hex())

    check_payment_command_model(
        receiver_status, sender_status, TransactionStatus.PENDING
    )

    updated_status = Status.ready_for_settlement
    storage.update_payment_command_sender_status(REFERENCE_ID, updated_status)

    check_payment_command_model(
        receiver_status, updated_status, TransactionStatus.OFF_CHAIN_OUTBOUND
    )


def check_payment_command_model(
    receiver_status, updated_status, expected_command_status
):
    model = storage.get_payment_command(REFERENCE_ID)

    assert model
    assert model.reference_id == REFERENCE_ID
    assert model.sender_address == MY_ADDRESS
    assert model.sender_status == updated_status
    assert model.receiver_address == OTHER_ADDRESS
    assert model.receiver_status == receiver_status
    assert model.amount == AMOUNT
    assert model.status == expected_command_status


def check_payment_command(expected_my_actor_address=context.get().config.vasp_address):
    payment_command = pc_service.get_payment_command(REFERENCE_ID)
    my_actor_address, _ = identifier.decode_account(
        payment_command.my_actor_address, context.get().config.diem_address_hrp()
    )

    assert payment_command
    assert payment_command.reference_id() == REFERENCE_ID
    assert payment_command.opponent_address() == OTHER_ADDRESS
    assert (
        my_actor_address.to_hex() == expected_my_actor_address
    ), f"{my_actor_address.to_hex()} != {expected_my_actor_address}"
    assert payment_command.payment.action.action == ACTION_CHARGE
    assert payment_command.payment.action.amount == AMOUNT
    assert payment_command.payment.action.currency == DiemCurrency.XUS
    assert payment_command.payment.receiver.status.status == Status.none
    assert payment_command.payment.sender.status.status == Status.none
