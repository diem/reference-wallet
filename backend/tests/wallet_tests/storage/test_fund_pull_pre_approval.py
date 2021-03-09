from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import (
    OneFundsPullPreApproval,
)
from wallet.services.offchain.fund_pull_pre_approval_sm import Role
from wallet.storage import (
    db_session,
    get_command_by_id,
    update_command,
)

FUNDS_PULL_PRE_APPROVAL_ID = "5fc49fa0-5f2a-4faa-b391-ac1652c57e4d"


def test_update_at(random_bech32_address, my_user):
    OneFundsPullPreApproval.run(
        db_session=db_session,
        account_id=my_user.account_id,
        address=random_bech32_address,
        biller_address=my_user.address,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status="pending",
        role=Role.PAYEE,
    )

    command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    created_at = command.created_at
    updated_at = command.updated_at

    command.status = "valid"

    update_command(command)

    updated_command = get_command_by_id(FUNDS_PULL_PRE_APPROVAL_ID)

    assert updated_command.updated_at != updated_at
    assert updated_command.updated_at > updated_at
    assert updated_command.created_at == created_at
    assert updated_command.status == "valid"
