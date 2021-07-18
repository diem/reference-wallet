from typing import Optional

from flask import Response
from wallet.services.offchain import p2m_payment as payment_service
from wallet.services.offchain.p2m_payment import (
    P2MPaymentNotFoundError,
    P2MPaymentStatus,
)
from werkzeug.test import Client

CURRENCY = "XUS"
ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
ADDRESS_2 = "tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd"
ADDRESS_3 = "tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5"
REFERENCE_ID = "c6f7e351-e1c3-4da7-9310-4e87296febf2"
REFERENCE_ID_2 = "dbcb698a-22a8-4dac-8710-668cdfdd045e"
CID = "1cea3243-4ea6-44b2-8590-ec5bf4a101b1"
CHARGE_ACTION = "charge"
AMOUNT = 200_000_000
EXPIRATION = 1802010490
DEMO = False


class TestGetPaymentDetails:
    def test_get_payment_details_exist_object(
        self, authorized_client: Client, mock_method
    ) -> None:
        MERCHANT_NAME = "Bond's Pet Store"
        mock_method(
            payment_service,
            "get_payment_details",
            will_return=payment_service.PaymentDetails(
                vasp_address=ADDRESS,
                reference_id=REFERENCE_ID,
                merchant_name=MERCHANT_NAME,
                action=CHARGE_ACTION,
                currency=CURRENCY,
                amount=AMOUNT,
                expiration=EXPIRATION,
                demo=DEMO,
                status=P2MPaymentStatus.READY_FOR_USER,
            ),
        )
        rv: Response = authorized_client.get(
            f"/offchain/query/payment_details?reference_id={REFERENCE_ID}&vasp_address={ADDRESS}",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        assert rv.get_json()["action"] == CHARGE_ACTION
        assert rv.get_json()["amount"] == AMOUNT
        assert rv.get_json()["currency"] == CURRENCY
        assert rv.get_json()["expiration"] == EXPIRATION
        assert rv.get_json()["merchant_name"] == MERCHANT_NAME
        assert rv.get_json()["reference_id"] == REFERENCE_ID
        assert rv.get_json()["vasp_address"] == ADDRESS

    def test_get_payment_details_not_exist_object(
        self, authorized_client: Client, mock_method
    ) -> None:
        mock_method(payment_service, "get_payment_details", will_return=None)

        rv: Response = authorized_client.get(
            f"/offchain/query/payment_details?reference_id={REFERENCE_ID}&vasp_address={ADDRESS}",
        )

        assert rv.status_code == 404
        assert (
            rv.get_json()["error"]
            == f"Failed finding payment details for reference id {REFERENCE_ID}"
        )


class TestAddPayment:
    def test_add_payment(self, authorized_client: Client, mock_method):
        mock_method(
            payment_service,
            "add_new_payment",
            will_return=None,
        )

        rv: Response = authorized_client.post(
            "/offchain/payment",
            json={
                "vasp_address": ADDRESS,
                "reference_id": REFERENCE_ID,
                "merchant_name": "Bond & Gurki Pet Store",
                "action": CHARGE_ACTION,
                "currency": "XUS",
                "amount": 1000,
                "expiration": EXPIRATION,
            },
        )

        assert rv.status_code == 204, rv.get_data()


class TestApproveP2MPayment:
    def test_payment_not_found(self, authorized_client: Client, mock_method):
        mock_method(
            payment_service, "approve_payment", will_raise=P2MPaymentNotFoundError
        )

        rv: Response = authorized_client.post(
            f"/offchain/payment/{REFERENCE_ID}/actions/approve",
            json={"init_offchain_required": False},
        )

        assert rv.status_code == 404, rv.get_data()

    def test_successful_payment(self, authorized_client: Client, mock_method):
        mock_method(payment_service, "approve_payment", will_return=None)

        rv: Response = authorized_client.post(
            f"/offchain/payment/{REFERENCE_ID}/actions/approve",
            json={"init_offchain_required": False},
        )

        assert rv.status_code == 204, rv.get_data()


class TestRejectP2MPayment:
    def test_payment_not_found(self, authorized_client: Client, mock_method):
        mock_method(
            payment_service, "reject_payment", will_raise=P2MPaymentNotFoundError
        )

        rv: Response = authorized_client.post(
            f"/offchain/payment/{REFERENCE_ID}/actions/reject",
            json={"init_offchain_required": False},
        )

        assert rv.status_code == 404, rv.get_data()

    def test_successful_payment(self, authorized_client: Client, mock_method):
        mock_method(payment_service, "reject_payment", will_return=None)

        rv: Response = authorized_client.post(
            f"/offchain/payment/{REFERENCE_ID}/actions/reject",
        )

        assert rv.status_code == 204, rv.get_data()
