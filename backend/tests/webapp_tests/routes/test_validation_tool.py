import json
import uuid
from typing import Optional

import pytest
from flask import Response
from flask.testing import Client
from wallet.services import validation_tool as validation_tool_service

FUNDS_PRE_APPROVAL_ID = str(uuid.uuid4())


@pytest.fixture
def mock_send_consent_request(monkeypatch):
    def mock(
        user_account_id,
        address,
        expiration_time,
        description,
        max_cumulative_amount,
        currency,
    ) -> Optional[str]:
        return FUNDS_PRE_APPROVAL_ID

    monkeypatch.setattr(validation_tool_service, "send_consent_request", mock)


class TestCreateConsentRequest:
    def test_send_consent_request(
        self, authorized_client: Client, mock_send_consent_request
    ) -> None:
        # address: "64b9dd1e5e56efb0c67e95b8bbecdfb4", sub_address: "9e8a79160e500d01"
        rv: Response = authorized_client.post(
            "/validation/consent",
            json={
                "address": "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc",
                "experation_time": 27345,
                "description": "Test create consent request",
                "max_cumulative_amount": 10000,
            },
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        funds_pre_approval_id = rv.get_json()["funds_pre_approval_id"]
        assert funds_pre_approval_id == FUNDS_PRE_APPROVAL_ID
