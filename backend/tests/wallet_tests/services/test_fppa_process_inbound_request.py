#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import time

import pytest
from diem import identifier, LocalAccount, offchain
from diem.offchain import FundPullPreApprovalStatus
from diem_utils.types.currencies import FiatCurrency, DiemCurrency

import context
import wallet.services.offchain as offchain_service
from wallet.services.account import generate_new_subaddress
from wallet.services.fund_pull_pre_approval_sm import (
    FundsPullPreApprovalStateError,
    Role,
)
from wallet.storage import (
    db_session,
    get_command_by_id,
    User,
    Account,
)
from wallet.types import RegistrationStatus

from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import (
    OneFundsPullPreApproval,
)


FUNDS_PULL_PRE_APPROVAL_ID = "5fc49fa0-5f2a-4faa-b391-ac1652c57e4d"
currency = DiemCurrency.XUS


class MyUser:
    def __init__(self):
        self.account_id = self._generate_mock_user().account_id
        self.address = self._generate_my_address(self.account_id)

    @staticmethod
    def _generate_mock_user():
        username = "test_user"

        user = User(
            username=username,
            registration_status=RegistrationStatus.Approved,
            selected_fiat_currency=FiatCurrency.USD,
            selected_language="en",
            password_salt="123",
            password_hash="deadbeef",
        )
        user.account = Account(name=username)
        db_session.add(user)
        db_session.commit()

        return user

    @staticmethod
    def _generate_my_address(account_id):
        sub_address = generate_new_subaddress(account_id)

        return identifier.encode_account(
            context.get().config.vasp_address,
            sub_address,
            context.get().config.diem_address_hrp(),
        )


@pytest.fixture
def my_user():
    return MyUser()


@pytest.fixture
def random_bech32_address():
    return identifier.encode_account(
        LocalAccount.generate().account_address,
        identifier.gen_subaddress(),
        context.get().config.diem_address_hrp(),
    )


@pytest.fixture
def process_inbound_command(mock_method):
    def process_inbound_command_builder(request_sender_address, command_properties):
        return ProcessInboundCommand(
            mock_method, request_sender_address, command_properties
        )

    return process_inbound_command_builder


class ProcessInboundCommand:
    def __init__(self, mock_method, request_sender_address, command_properties: dict):
        self.fppa_id = command_properties.get("funds_pull_pre_approval_id")
        self.command = self.generate_fppa_command(**command_properties)

        self.request_sender_address = request_sender_address
        self.command_properties = command_properties

        mock_method(
            context.get().offchain_client,
            "process_inbound_request",
            will_return=self.command,
        )

    def assert_command_stored(self):
        _ = b"Unused because process_inbound_request is mocked"
        code, resp = offchain_service.process_inbound_command(
            request_sender_address=self.request_sender_address, request_body_bytes=_
        )
        assert code == 200
        assert resp

        command_in_db = get_command_by_id(self.fppa_id)
        for prop, value in self.command_properties.items():
            assert getattr(command_in_db, prop) == value

    def assert_error_raised(self):
        with pytest.raises(FundsPullPreApprovalStateError):
            _ = b"Unused because process_inbound_request is mocked"
            offchain_service.process_inbound_command(self.request_sender_address, _)

    @classmethod
    def generate_fppa_command(
        cls,
        address,
        biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        status=FundPullPreApprovalStatus.pending,
    ):
        funds_pull_pre_approval = cls.generate_fppa_object(
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            max_cumulative_unit=max_cumulative_unit,
            max_cumulative_unit_value=max_cumulative_unit_value,
            status=status,
        )

        return offchain.FundsPullPreApprovalCommand(
            my_actor_address=address, funds_pull_pre_approval=funds_pull_pre_approval
        )

    @staticmethod
    def generate_fppa_object(
        address,
        biller_address,
        funds_pull_pre_approval_id,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        status=FundPullPreApprovalStatus.pending,
    ):
        funds_pull_pre_approval = offchain.FundPullPreApprovalObject(
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            address=address,
            biller_address=biller_address,
            scope=offchain.FundPullPreApprovalScopeObject(
                type=offchain.FundPullPreApprovalType.consent,
                expiration_timestamp=int(time.time()) + 30,
                max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                    unit=max_cumulative_unit,
                    value=max_cumulative_unit_value,
                    max_amount=offchain.CurrencyObject(
                        amount=10_000_000_000_000, currency=currency
                    ),
                ),
            ),
            status=status,
            description="test",
        )
        return funds_pull_pre_approval


def test_process_inbound_command_as_payer_with_incoming_pending_and_no_record_in_db(
    mock_method, my_user, random_bech32_address, process_inbound_command
):
    process_inbound_command(
        request_sender_address=my_user.address,
        command_properties=dict(
            address=my_user.address,
            biller_address=random_bech32_address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=FundPullPreApprovalStatus.pending,
        ),
    ).assert_command_stored()


def test_process_inbound_command_as_payer_with_incoming_pending_while_record_db_exist(
    mock_method, my_user, random_bech32_address, process_inbound_command
):
    biller_address = random_bech32_address

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=my_user.address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        role=Role.PAYER,
    )

    process_inbound_command(
        request_sender_address=my_user.address,
        command_properties=dict(
            address=my_user.address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            max_cumulative_unit="month",
            max_cumulative_unit_value=2,
        ),
    ).assert_command_stored()


@pytest.mark.parametrize(
    "new_status",
    [
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.closed,
    ],
)
def test_failure_as_payer_without_record_in_db(
    new_status, my_user, random_bech32_address, process_inbound_command
):
    process_inbound_command(
        request_sender_address=my_user.address,
        command_properties=dict(
            address=my_user.address,
            biller_address=random_bech32_address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_error_raised()


@pytest.mark.parametrize(
    "new_status,stored_status",
    [
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.valid),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.closed),
    ],
)
def test_success_as_payer_with_record_in_db(
    new_status, stored_status, my_user, random_bech32_address, process_inbound_command
):
    biller_address = random_bech32_address

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=my_user.address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=stored_status,
        role=Role.PAYER,
    )

    process_inbound_command(
        request_sender_address=my_user.address,
        command_properties=dict(
            address=my_user.address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_command_stored()


@pytest.mark.parametrize(
    "new_status,stored_status",
    [
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.rejected),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.rejected),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.valid),
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.closed),
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.pending),
    ],
)
def test_failure_as_payer_with_record_in_db(
    new_status, stored_status, my_user, random_bech32_address, process_inbound_command
):
    biller_address = random_bech32_address

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=my_user.address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=stored_status,
        role=Role.PAYER,
    )

    process_inbound_command(
        request_sender_address=my_user.address,
        command_properties=dict(
            address=my_user.address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_error_raised()


@pytest.mark.parametrize(
    "new_status",
    [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.closed,
    ],
)
def test_failure_as_payee_without_record_in_db(
    new_status, my_user, random_bech32_address, process_inbound_command
):
    address = random_bech32_address

    process_inbound_command(
        request_sender_address=address,
        command_properties=dict(
            address=address,
            biller_address=my_user.address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_error_raised()


@pytest.mark.parametrize(
    "new_status,stored_status",
    [
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.rejected),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.valid),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.valid),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.closed),
    ],
)
def test_success_as_payee_with_record_in_db(
    new_status, stored_status, my_user, random_bech32_address, process_inbound_command
):
    address = random_bech32_address

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=address,
        biller_address=my_user.address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=stored_status,
        role=Role.PAYEE,
    )

    process_inbound_command(
        request_sender_address=address,
        command_properties=dict(
            address=address,
            biller_address=my_user.address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_command_stored()


@pytest.mark.parametrize(
    "new_status,stored_status",
    [
        (FundPullPreApprovalStatus.pending, FundPullPreApprovalStatus.pending),
        (FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.closed),
        (FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.rejected),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.rejected),
        (FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.closed),
    ],
)
def test_failure_as_payee_with_record_in_db(
    new_status, stored_status, my_user, random_bech32_address, process_inbound_command
):
    address = random_bech32_address

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=address,
        biller_address=my_user.address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=stored_status,
        role=Role.PAYEE,
    )

    process_inbound_command(
        request_sender_address=address,
        command_properties=dict(
            address=address,
            biller_address=my_user.address,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            status=new_status,
        ),
    ).assert_error_raised()