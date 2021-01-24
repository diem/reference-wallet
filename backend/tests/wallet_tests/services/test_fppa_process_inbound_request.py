#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import time

import context
import pytest
from diem import identifier, LocalAccount, offchain
from diem.offchain import FundPullPreApprovalStatus
from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import (
    OneFundsPullPreApproval,
)
from diem_utils.types.currencies import FiatCurrency, DiemCurrency
from wallet.services.account import generate_new_subaddress
from wallet.services.fund_pull_pre_approval_sm import (
    FundsPullPreApprovalStateError,
    Role,
)
from wallet.services.offchain import (
    process_inbound_command,
)
from wallet.storage import (
    db_session,
    get_command_by_id,
    User,
    Account,
)
from wallet.types import RegistrationStatus


FUNDS_PULL_PRE_APPROVAL_ID = "5fc49fa0-5f2a-4faa-b391-ac1652c57e4d"
currency = DiemCurrency.XUS


def test_process_inbound_command_as_payer_with_incoming_pending_and_no_record_in_db(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address


def test_process_inbound_command_as_payer_with_incoming_pending_while_record_db_exist(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        max_cumulative_unit="month",
        max_cumulative_unit_value=2,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.max_cumulative_unit == "month"
    assert command_in_db.max_cumulative_unit_value == 2


def test_process_inbound_command_as_payer_with_incoming_reject_and_no_record_in_db(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payer_with_incoming_reject_while_record_db_exist(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payer_with_incoming_valid_and_no_record_in_db(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payer_with_incoming_valid_while_record_db_exist(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payer_with_incoming_closed_and_no_record_in_db(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payer_with_incoming_closed_while_record_db_exist_with_valid_status(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.closed


def test_process_inbound_command_as_payer_with_incoming_closed_while_record_db_exist_with_pending_status(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.closed


def test_process_inbound_command_as_payer_with_incoming_closed_while_record_db_exist_with_rejected_status(
    mock_method,
):
    user = generate_mock_user()
    address = generate_my_address(user)
    biller_address = generate_address()

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
        role=Role.PAYER,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_pending_and_no_record_in_db(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_pending_while_record_db_exist(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        max_cumulative_unit="month",
        max_cumulative_unit_value=2,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_reject_and_no_record_in_db(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_reject_while_record_db_exist_with_pending_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.rejected


def test_process_inbound_command_as_payee_with_incoming_reject_while_record_db_exist_with_valid_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_reject_while_record_db_exist_with_rejected_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_reject_while_record_db_exist_with_closed_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_valid_and_no_record_in_db(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_valid_while_record_db_exist_with_pending_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.valid


def test_process_inbound_command_as_payee_with_incoming_valid_while_record_db_exist_with_valid_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_valid_while_record_db_exist_with_rejected_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_valid_while_record_db_exist_with_closed_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_closed_and_no_record_in_db(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_closed_while_record_db_exist_with_valid_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.closed


def test_process_inbound_command_as_payee_with_incoming_closed_while_record_db_exist_with_pending_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    unused = b"Unused because process_inbound_request is mocked"
    code, resp = process_inbound_command(address, unused)
    assert code == 200
    assert resp
    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.address == address
    assert command_in_db.biller_address == biller_address
    assert command_in_db.status == FundPullPreApprovalStatus.closed


def test_process_inbound_command_as_payee_with_incoming_closed_while_record_db_exist_with_rejected_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def test_process_inbound_command_as_payee_with_incoming_closed_while_record_db_exist_with_closed_status(
    mock_method,
):
    address = generate_address()
    biller_user = generate_mock_user()
    biller_address = generate_my_address(biller_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=biller_user.account_id,
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
        role=Role.PAYEE,
    )

    cmd = generate_funds_pull_pre_approval_command(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )

    with pytest.raises(FundsPullPreApprovalStateError):
        unused = b"Unused because process_inbound_request is mocked"
        process_inbound_command(address, unused)


def generate_funds_pull_pre_approval_command(
    address,
    biller_address,
    funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
    max_cumulative_unit="week",
    max_cumulative_unit_value=1,
    status=FundPullPreApprovalStatus.pending,
):
    funds_pull_pre_approval = generate_fund_pull_pre_approval_object(
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


def generate_fund_pull_pre_approval_object(
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


def generate_mock_user(user_name="test_user"):
    user = User(
        username=user_name,
        registration_status=RegistrationStatus.Approved,
        selected_fiat_currency=FiatCurrency.USD,
        selected_language="en",
        password_salt="123",
        password_hash="deadbeef",
    )
    user.account = Account(name=user_name)
    db_session.add(user)
    db_session.commit()

    return user


def generate_my_address(user):
    sub_address = generate_new_subaddress(user.account_id)

    return identifier.encode_account(
        context.get().config.vasp_address,
        sub_address,
        context.get().config.diem_address_hrp(),
    )


def generate_address():
    return identifier.encode_account(
        LocalAccount.generate().account_address,
        identifier.gen_subaddress(),
        context.get().config.diem_address_hrp(),
    )
