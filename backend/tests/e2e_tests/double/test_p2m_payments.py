import logging

import pytest

from .. import UserClient, LRW_WEB_1, LRW_WEB_2


"""
This e2e tests purpose is to test the p2m offchain communication between funds sender and receiver.
In the real world the communication between the receiver and sender will begin with a link or QR code that the receiver
supply to the sender and contains the payment unique reference id and the receiver onchain address. 
Therefore, all the test are starting with 'receiver.create_payment_as_receiver()' to simulate the receiver


To simulate the link\QR code the test beging with creation of the payment on the receiver side. In real world scenario, 
at this point the link\QR code will be suplay to the sender in one of the available platforms.
As response (clicking the link or scan the QR code) the sender will create the payment on his side.
The creation of the payment in the sender side will trigger a GetPaymentInfo offchain request,
when the offchain response will arrive succefully with the full payment information from the receiver, the wallet will be
able to display the full data of the payment to the user, which in his turn could decied if he wish to approve or reject the payment. 

1. test_reject_p2m_charge_payment testing the scenario which in the user decided to reject the payment. The user rejection will trigger a AbortPayment offchain command
"""


def test_reject_p2m_charge_payment():
    sender = UserClient.create(LRW_WEB_1, "transfer_test_user1")
    receiver = UserClient.create(LRW_WEB_2, "transfer_test_user2")

    # receiver create payment
    reference_id, vasp_address = receiver.create_payment_as_receiver()

    logging.info(f"reference_id: {reference_id}, vasp_address: {vasp_address}")

    # sender create payment base on receiver information
    payment = sender.create_payment_as_sender(reference_id, vasp_address)

    # sender reject payment
    sender.reject_payment(reference_id)

    logging.info(f"payment: {payment}")

    pytest.fail()
