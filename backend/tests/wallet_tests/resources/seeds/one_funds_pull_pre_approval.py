import time
import uuid

from diem.offchain import FundPullPreApprovalStatus
from diem_utils.types.currencies import DiemCurrency
from wallet.services.offchain import Role
from wallet.storage.models import FundsPullPreApprovalCommand

ADDRESS = "257e50b131150fdb56aeab4ebe4ec2b9"
BILLER_ADDRESS = "176b73399b04d9231769614cf22fb5df"


class OneFundsPullPreApproval:
    @staticmethod
    def run(
        db_session,
        funds_pull_pre_approval_id=str(uuid.uuid4()),
        status=FundPullPreApprovalStatus.valid,
    ) -> FundsPullPreApprovalCommand:
        command = FundsPullPreApprovalCommand(
            account_id=1,
            address=ADDRESS,
            biller_address=BILLER_ADDRESS,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time() + 30),
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=DiemCurrency.XUS,
            max_transaction_amount=10_000_000,
            max_transaction_amount_currency=DiemCurrency.XUS,
            description="OneFundsPullPreApprovalRun",
            status=status,
            role=Role.PAYER,
        )

        db_session.add(command)
        db_session.commit()

        return command
