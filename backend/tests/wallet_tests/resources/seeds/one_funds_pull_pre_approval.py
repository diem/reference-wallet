import uuid
from datetime import datetime

from offchain import FundPullPreApprovalStatus
from diem_utils.types.currencies import DiemCurrency
from wallet.services.offchain.fund_pull_pre_approval import Role
from wallet.storage.models import FundsPullPreApprovalCommand

ADDRESS = "tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf"
ADDRESS_2 = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"

BILLER_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"

TIMESTAMP = 1802010490
EXPIRED_TIMESTAMP = 1581085690


class OneFundsPullPreApproval:
    @staticmethod
    def run(
        db_session,
        biller_address=BILLER_ADDRESS,
        address=ADDRESS,
        funds_pull_pre_approval_id=str(uuid.uuid4()),
        status=FundPullPreApprovalStatus.valid,
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        account_id=1,
        role=Role.PAYER,
        offchain_sent=False,
    ) -> FundsPullPreApprovalCommand:
        command = FundsPullPreApprovalCommand(
            account_id=account_id,
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=datetime(2027, 3, 3, 10, 10, 10),
            max_cumulative_unit=max_cumulative_unit,
            max_cumulative_unit_value=max_cumulative_unit_value,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=DiemCurrency.XUS,
            max_transaction_amount=10_000_000,
            max_transaction_amount_currency=DiemCurrency.XUS,
            description="OneFundsPullPreApprovalRun",
            status=status,
            role=role,
            offchain_sent=offchain_sent,
        )

        db_session.add(command)
        db_session.commit()

        return command
