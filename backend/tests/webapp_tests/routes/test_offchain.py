import json
from typing import Optional, List

import pytest
from flask import Response
from flask.testing import Client
from wallet.services import offchain as offchain_service

ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"


@pytest.fixture
def mock_get_payment_command_json(monkeypatch):
    def mock(transaction_id: int) -> Optional[str]:
        return json.loads(
            '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "payment": {'
            '"reference_id": "c6f7e351-e1c3-4da7-9310-4e87296febf2", "sender": {"address": '
            '"tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "status": {"status": "ready_for_settlement"}, '
            '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "3qflfqmo", "surname": '
            '"yph277u8", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
            '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
            '"tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd", "status": {"status": "ready_for_settlement"}, '
            '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "gug0fngi", "surname": '
            '"6mpcox8c", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
            '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
            '"currency": "XUS", "action": "charge", "timestamp": 1609064370}, "recipient_signature": '
            '"ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108"}, "inbound": false, "cid": "1cea3243-4ea6-44b2-8590-ec5bf4a101b1"} '
        )

    monkeypatch.setattr(offchain_service, "get_payment_command_json", mock)


class TestGetPaymentCommand:
    def test_get_payment_command_json(
        self, authorized_client: Client, mock_get_payment_command_json
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/query/payment_command/22",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        payment_command = rv.get_json()["payment_command"]
        assert payment_command is not None
        assert payment_command["my_actor_address"] == ADDRESS


@pytest.fixture
def mock_get_account_payment_commands(monkeypatch):
    def mock(account_id: int) -> List[str]:
        return [
            json.loads(
                '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "payment": {"reference_id": '
                '"c6f7e351-e1c3-4da7-9310-4e87296febf2", "sender": {"address": '
                '"tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "3qflfqmo", "surname": '
                '"yph277u8", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
                '"tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "gug0fngi", "surname": '
                '"6mpcox8c", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
                '"currency": "XUS", "action": "charge", "timestamp": 1609064370}, "recipient_signature": '
                '"ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108"}, '
                '"inbound": false, "cid": "1cea3243-4ea6-44b2-8590-ec5bf4a101b1"}'
            ),
            json.loads(
                '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5", "payment": {"reference_id": '
                '"dbcb698a-22a8-4dac-8710-668cdfdd045e", "sender": {"address": '
                '"tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "wb5xaftc", "surname": '
                '"aaogh8rp", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
                '"tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "nz45p518", "surname": '
                '"qs83qard", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
                '"currency": "XUS", "action": "charge", "timestamp": 1609064361}, "recipient_signature": '
                '"d84c2e733c9d68c869ad5e2bb155e8f5441c65312d47dfd5189abfb5037a160dcca770cd733284bae53847c0d6eb17afc31248453a7fcbe43c5b2f3eadd67208"}, '
                '"inbound": true, "cid": "3b6f2e01-2da0-4acb-ad74-631546edfba0"}'
            ),
        ]

    monkeypatch.setattr(offchain_service, "get_account_payment_commands", mock)


class TestGetAccountPaymentCommands:
    def test_get_account_payment_commands(
        self, authorized_client: Client, mock_get_account_payment_commands
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/query/payment_command",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        payment_commands = rv.get_json()["payment_commands"]
        assert payment_commands is not None
        assert len(payment_commands) == 2
        assert payment_commands[0]["my_actor_address"] == ADDRESS
