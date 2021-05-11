from typing import Optional

import pytest
from flask import Response
from wallet.services.offchain import payment as payment_service
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


@pytest.fixture
def mock_get_payment_details_exist_object(monkeypatch):
    def mock(
        account_id, reference_id, vasp_address
    ) -> Optional[payment_service.PaymentDetails]:
        return payment_service.PaymentDetails(
            vasp_address=ADDRESS,
            reference_id=REFERENCE_ID,
            merchant_name="Bond's Per Store",
            action=CHARGE_ACTION,
            currency=CURRENCY,
            amount=AMOUNT,
            expiration=EXPIRATION,
        )

    monkeypatch.setattr(payment_service, "get_payment_details", mock)


@pytest.fixture
def mock_get_payment_details_not_exist_object(monkeypatch):
    def mock(
        account_id, reference_id, vasp_address
    ) -> Optional[payment_service.PaymentDetails]:
        return None

    monkeypatch.setattr(payment_service, "get_payment_details", mock)


class TestGetPaymentDetails:
    def test_get_payment_details_exist_object(
        self, authorized_client: Client, mock_get_payment_details_exist_object
    ) -> None:
        rv: Response = authorized_client.get(
            f"/offchain/query/payment_details?reference_id={REFERENCE_ID}&vasp_address={ADDRESS}",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        assert rv.get_json()["action"] == CHARGE_ACTION
        assert rv.get_json()["amount"] == AMOUNT
        assert rv.get_json()["currency"] == CURRENCY
        assert rv.get_json()["expiration"] == EXPIRATION
        assert rv.get_json()["merchant_name"] == "Bond's Per Store"
        assert rv.get_json()["reference_id"] == REFERENCE_ID
        assert rv.get_json()["vasp_address"] == ADDRESS

    def test_get_payment_details_not_exist_object(
        self, authorized_client: Client, mock_get_payment_details_not_exist_object
    ) -> None:
        rv: Response = authorized_client.get(
            f"/offchain/query/payment_details?reference_id={REFERENCE_ID}&vasp_address={ADDRESS}",
        )

        assert rv.status_code == 404
        assert (
            rv.get_json()["error"]
            == f"Failed finding payment details for reference id {REFERENCE_ID}"
        )


@pytest.fixture()
def mock_add_payment(monkeypatch):
    def mock(
        account_id,
        reference_id,
        vasp_address,
        merchant_name,
        action,
        currency,
        amount,
        expiration,
    ) -> None:
        return

    monkeypatch.setattr(payment_service, "add_new_payment", mock)


class TestAddPayment:
    def test_add_payment(self, authorized_client: Client, mock_add_payment):
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
