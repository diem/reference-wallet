import logging

import pytest
from wallet.services.offchain.p2m_payment import P2MPaymentStatus

from .. import UserClient, LRW_WEB_1, LRW_WEB_2

"""
This e2e tests purpose is to test the p2m offchain communication between funds sender and receiver.
In the real world the communication between the receiver and sender always begin on the receiver side which create
the payment for internal usage and generate a link or QR code that contains the payment unique reference id 
and the receiver onchain address and supply it to the sender.
Therefore, all the tests are starting with the following:
    1. 'receiver.create_payment_as_receiver()' to simulate the receiver internal payment creation.
    2. 'sender.create_payment_as_sender(reference_id, vasp_address)' to simulate the state which in the sender 
    clicked the link or scanned the QR code. The creation of the payment on the sender side will trigger 
    a GetPaymentInfo offchain request. When the offchain 'GetInfoCommandResponse' return successfully from
    the receiver to the sender with all the payment information, the sender display the payment to the user, 
    which then can decide if he wish to approve or reject the payment. 
"""


def test_reject_p2m_charge_payment():
    # create sender and receiver
    sender = UserClient.create(LRW_WEB_1, "transfer_test_user1")
    receiver = UserClient.create(LRW_WEB_2, "transfer_test_user2")

    # receiver create payment
    reference_id, vasp_address = receiver.create_payment_as_receiver()
    receiver_payment = receiver.get_payment_details(reference_id, vasp_address)

    # sender create payment base on receiver information
    sender_payment = sender.create_payment_as_sender(reference_id, vasp_address)

    compare(receiver_payment, sender_payment, "action")
    compare(receiver_payment, sender_payment, "amount")
    compare(receiver_payment, sender_payment, "expiration")
    compare(receiver_payment, sender_payment, "merchant_name")
    compare_to_expected_value(
        receiver_payment, sender_payment, "reference_id", reference_id
    )
    compare_to_expected_value(
        receiver_payment, sender_payment, "status", P2MPaymentStatus.READY_FOR_USER
    )
    compare_to_expected_value(
        receiver_payment, sender_payment, "vasp_address", vasp_address
    )

    # sender reject payment
    sender.reject_payment(reference_id)

    sender_payment_after_abort = sender.get_payment_details(reference_id, vasp_address)

    receiver_payment_after_abort = receiver.get_payment_details(
        reference_id, vasp_address
    )

    pytest.fail()
