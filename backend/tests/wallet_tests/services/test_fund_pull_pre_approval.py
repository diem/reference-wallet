# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time

import context
import pytest
from diem import identifier, LocalAccount, offchain
from diem.offchain import (
    FundPullPreApprovalStatus,
)
from diem_utils.types.currencies import FiatCurrency, DiemCurrency
from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import (
    OneFundsPullPreApproval,
)
from wallet.services.account import (
    generate_new_subaddress,
)
from wallet.services.fund_pull_pre_approval import (
    create_and_approve,
    approve,
    Role,
    FundsPullPreApprovalError,
    close,
    reject,
    get_combinations,
    all_combinations,
    process_funds_pull_pre_approvals_requests,
    preapproval_command_to_model,
    get_command_from_bech32,
)
from wallet.services.offchain import (
    process_inbound_command,
)
from wallet.storage import (
    db_session,
    User,
    Account,
    get_command_by_id,
    update_command,
)
from wallet.types import RegistrationStatus

CID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"
FUNDS_PULL_PRE_APPROVAL_ID = "5fc49fa0-5f2a-4faa-b391-ac1652c57e4d"
currency = DiemCurrency.XUS


def test_approve_but_no_command_in_db():
    with pytest.raises(FundsPullPreApprovalError, match=r"Could not find command .*"):
        approve(FUNDS_PULL_PRE_APPROVAL_ID)


def test_close_but_no_command_in_db():
    with pytest.raises(FundsPullPreApprovalError, match=r"Could not find command .*"):
        close(FUNDS_PULL_PRE_APPROVAL_ID)


def test_reject_but_no_command_in_db():
    with pytest.raises(FundsPullPreApprovalError, match=r"Could not find command .*"):
        reject(FUNDS_PULL_PRE_APPROVAL_ID)


def test_approve_happy_flow():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.pending

    approve(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.valid


def test_close_happy_flow():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.pending

    close(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.closed


def test_reject_happy_flow():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.pending

    reject(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.rejected


def test_approve_while_command_with_pending_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    approve(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.valid


def test_close_while_command_with_pending_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    close(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.closed


def test_reject_while_command_with_pending_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    reject(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.rejected


def test_approve_while_command_with_valid_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not approve command with status .*"
    ):
        approve(FUNDS_PULL_PRE_APPROVAL_ID)


def test_close_while_command_with_valid_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )

    close(FUNDS_PULL_PRE_APPROVAL_ID)

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.closed


def test_reject_while_command_with_valid_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.valid,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not reject command with status .*"
    ):
        reject(FUNDS_PULL_PRE_APPROVAL_ID)


def test_approve_while_command_with_closed_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not approve command with status .*"
    ):
        approve(FUNDS_PULL_PRE_APPROVAL_ID)


def test_close_while_command_with_closed_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not close command with status .*"
    ):
        close(FUNDS_PULL_PRE_APPROVAL_ID)


def test_reject_while_command_with_closed_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not reject command with status .*"
    ):
        reject(FUNDS_PULL_PRE_APPROVAL_ID)


def test_approve_while_command_with_rejected_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not approve command with status .*"
    ):
        approve(FUNDS_PULL_PRE_APPROVAL_ID)


def test_close_while_command_with_rejected_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not close command with status .*"
    ):
        close(FUNDS_PULL_PRE_APPROVAL_ID)


def test_reject_while_command_with_rejected_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.rejected,
    )

    with pytest.raises(
        FundsPullPreApprovalError, match=r"Could not reject command with status .*"
    ):
        reject(FUNDS_PULL_PRE_APPROVAL_ID)


def test_create_and_approve_happy_flow():
    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command is None

    user = generate_mock_user()

    create_and_approve(
        account_id=user.account.id,
        biller_address=generate_my_address(user),
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        funds_pull_pre_approval_type="consent",
        expiration_timestamp=int(time.time() + 30),
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        max_cumulative_amount=10_000_000_000,
        max_cumulative_amount_currency=currency,
        max_transaction_amount=10_000,
        max_transaction_amount_currency=currency,
        description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
    )

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.valid
    assert command.role == Role.PAYER


def test_create_and_approve_with_expired_expiration_timestamp():
    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command is None

    with pytest.raises(
        ValueError,
        match="expiration timestamp must be in the future",
    ):
        create_and_approve(
            account_id=1,
            biller_address=generate_address(),
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time() - 30),
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=currency,
            max_transaction_amount=10_000,
            max_transaction_amount_currency=currency,
            description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
        )


def test_create_and_approve_while_command_already_exist_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    with pytest.raises(
        FundsPullPreApprovalError,
        match=f"Command with id {FUNDS_PULL_PRE_APPROVAL_ID} already exist in db",
    ):
        create_and_approve(
            account_id=1,
            biller_address=generate_address(),
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time() + 30),
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=currency,
            max_transaction_amount=10_000,
            max_transaction_amount_currency=currency,
            description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
        )


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

    code, resp = process_inbound_command(address, cmd)
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

    code, resp = process_inbound_command(address, cmd)
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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    code, resp = process_inbound_command(address, cmd)
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

    code, resp = process_inbound_command(address, cmd)
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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    code, resp = process_inbound_command(address, cmd)
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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


def test_process_inbound_command_as_payee_with_incoming_valid_while_record_db_exist_with_pending_status(
    mock_method,
):
    """
    Tries to update existing "valid" command to "pending".
    """
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

    code, resp = process_inbound_command(address, cmd)
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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    code, resp = process_inbound_command(address, cmd)
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

    code, resp = process_inbound_command(address, cmd)
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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


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

    with pytest.raises(
        FundsPullPreApprovalError,
    ):
        process_inbound_command(address, cmd)


def test_process_inbound_command_as_both__happy_flow(mock_method):
    payer_user = generate_mock_user(user_name="payer_user")
    payer_bech32 = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    payee_bech32 = generate_my_address(payee_user)

    # first step - payee initiate completely new funds pull pre approval request
    # --------------------------------------------------------------------------
    payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32)
    # second step - payer approve the funds pull pre approval request
    # ---------------------------------------------------------------
    payer_response_to_new_request_check(mock_method, payee_bech32, payer_bech32, payer_user, FundPullPreApprovalStatus.valid)
    # third step - payer close the funds pull pre approval request
    # ------------------------------------------------------------
    payer_close_request_check(mock_method, payee_bech32, payer_bech32, payer_user)


def test_process_inbound_command_as_both__reject_by_payer(mock_method):
    payer_user = generate_mock_user(user_name="payer_user")
    payer_bech32 = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    payee_bech32 = generate_my_address(payee_user)

    # first step - payee initiate completely new funds pull pre approval request
    # --------------------------------------------------------------------------
    payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32)
    # second step - payer reject the funds pull pre approval request
    # ---------------------------------------------------------------
    payer_response_to_new_request_check(mock_method, payee_bech32, payer_bech32, payer_user, FundPullPreApprovalStatus.rejected)


def test_process_inbound_command_as_both__payer_close_pending_request(mock_method):
    payer_user = generate_mock_user(user_name="payer_user")
    payer_bech32 = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    payee_bech32 = generate_my_address(payee_user)

    # first step - payee initiate completely new funds pull pre approval request
    # --------------------------------------------------------------------------
    payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32)
    # second step - payer close the funds pull pre approval request
    # ---------------------------------------------------------------
    payer_response_to_new_request_check(mock_method, payee_bech32, payer_bech32, payer_user, FundPullPreApprovalStatus.closed)


def test_process_inbound_command_as_both__payee_close_pending_request(mock_method):
    payer_user = generate_mock_user(user_name="payer_user")
    payer_bech32 = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    payee_bech32 = generate_my_address(payee_user)

    # first step - payee initiate completely new funds pull pre approval request
    # --------------------------------------------------------------------------
    payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32)
    # second step - payee close the funds pull pre approval request
    # ---------------------------------------------------------------
    payee_close_request_check(mock_method, payee_bech32, payee_user, payer_bech32)


def test_process_inbound_command_as_both__payee_close_valid_request(mock_method):
    payer_user = generate_mock_user(user_name="payer_user")
    payer_bech32 = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    payee_bech32 = generate_my_address(payee_user)

    # first step - payee initiate completely new funds pull pre approval request
    # --------------------------------------------------------------------------
    payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32)
    # second step - payer approve the funds pull pre approval request
    # ---------------------------------------------------------------
    payer_response_to_new_request_check(mock_method, payee_bech32, payer_bech32, payer_user, FundPullPreApprovalStatus.valid)
    # third step - payer close the funds pull pre approval request
    # ------------------------------------------------------------
    payee_close_request_check(mock_method, payee_bech32, payee_user, payer_bech32)


def payee_close_request_check(mock_method, payee_bech32, payee_user, payer_bech32):
    # payee generate closed command to payer
    cmd = generate_funds_pull_pre_approval_command(
        address=payer_bech32,
        biller_address=payee_bech32,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    # payee update his command to closed
    update_command(
        payee_user.account_id,
        preapproval_command_to_model(
            account_id=payee_user.account_id,
            command=cmd,
            role=Role.PAYEE,
        ),
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )
    code, resp = process_inbound_command(payee_bech32, cmd)
    assert code == 200
    assert resp
    payer_command_in_db = get_command_from_bech32(
        payer_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payer_command_in_db
    assert (
            payer_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.closed
    )
    payee_command_in_db = get_command_from_bech32(
        payee_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payee_command_in_db
    assert (
            payee_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.closed
    )


def payer_close_request_check(mock_method, payee_bech32, payer_bech32, payer_user):
    # payer generate closed command to payer
    cmd = generate_funds_pull_pre_approval_command(
        address=payer_bech32,
        biller_address=payee_bech32,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )
    # payer update his command to valid
    update_command(
        payer_user.account_id,
        preapproval_command_to_model(
            account_id=payer_user.account_id,
            command=cmd,
            role=Role.PAYER,
        ),
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )
    code, resp = process_inbound_command(payee_bech32, cmd)
    assert code == 200
    assert resp
    payer_command_in_db = get_command_from_bech32(
        payer_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payer_command_in_db
    assert (
            payer_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.closed
    )
    payee_command_in_db = get_command_from_bech32(
        payee_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payee_command_in_db
    assert (
            payee_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.closed
    )


def payer_response_to_new_request_check(mock_method, payee_bech32, payer_bech32, payer_user, response_status):
    # payer generate valid command to payer
    cmd = generate_funds_pull_pre_approval_command(
        address=payer_bech32,
        biller_address=payee_bech32,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=response_status,
    )
    # payer update his command to valid
    update_command(
        payer_user.account_id,
        preapproval_command_to_model(
            account_id=payer_user.account_id,
            command=cmd,
            role=Role.PAYER,
        ),
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )
    code, resp = process_inbound_command(payee_bech32, cmd)
    assert code == 200
    assert resp
    payer_command_in_db = get_command_from_bech32(
        payer_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payer_command_in_db
    assert (
            payer_command_in_db.funds_pull_pre_approval.status
            == response_status
    )
    payee_command_in_db = get_command_from_bech32(
        payee_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payee_command_in_db
    assert (
            payee_command_in_db.funds_pull_pre_approval.status
            == response_status
    )


def payee_initiate_completely_new_funds_pull_pre_approval_request_check(mock_method, payee_bech32, payee_user, payer_bech32):
    # payee generate command in DB before sending
    OneFundsPullPreApproval.run(
        db_session=db_session,
        address=payer_bech32,
        biller_address=payee_bech32,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
        account_id=payee_user.account_id,
        role=Role.PAYEE,
    )
    # payee generate pending command to payer
    cmd = generate_funds_pull_pre_approval_command(
        address=payer_bech32,
        biller_address=payee_bech32,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )
    mock_method(
        context.get().offchain_client,
        "process_inbound_request",
        will_return=cmd,
    )
    code, resp = process_inbound_command(payee_bech32, cmd)
    assert code == 200
    assert resp
    payer_command_in_db = get_command_from_bech32(
        payer_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payer_command_in_db
    assert (
            payer_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.pending
    )
    payee_command_in_db = get_command_from_bech32(
        payee_bech32, FUNDS_PULL_PRE_APPROVAL_ID
    )
    assert payee_command_in_db
    assert (
            payee_command_in_db.funds_pull_pre_approval.status
            == FundPullPreApprovalStatus.pending
    )


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


def test_role_calculation():
    actual_combinations = get_combinations()
    expected_combinations = set(all_combinations())

    for com in actual_combinations:
        expected_combinations.remove(com)

    assert len(expected_combinations) == 0, print_expected_combinations(
        expected_combinations
    )


def print_expected_combinations(expected_combinations):
    for comb in expected_combinations:
        print(comb)


def test_outgoing_commands(mock_method):
    offchain_client = context.get().offchain_client
    send_command_calls = mock_method(offchain_client, "send_command")

    payer_user = generate_mock_user(user_name="payer_user")
    address = generate_my_address(payer_user)
    payee_user = generate_mock_user(user_name="payee_user")
    biller_address = generate_my_address(payee_user)

    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        address=address,
        biller_address=biller_address,
        status=FundPullPreApprovalStatus.valid,
    )

    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert not command_in_db.offchain_sent

    # One command should be sent
    process_funds_pull_pre_approvals_requests()
    assert len(send_command_calls) == 1

    send_command_call = send_command_calls.pop()
    sent_cmd: FundPullPreApprovalObject = send_command_call[0].funds_pull_pre_approval
    assert sent_cmd.funds_pull_pre_approval_id == FUNDS_PULL_PRE_APPROVAL_ID
    assert sent_cmd.status == FundPullPreApprovalStatus.valid

    command_in_db = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)
    assert command_in_db.offchain_sent

    # No commands to send this time
    process_funds_pull_pre_approvals_requests()
    assert len(send_command_calls) == 0
