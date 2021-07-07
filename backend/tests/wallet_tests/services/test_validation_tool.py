#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from diem import offchain

from wallet.services.account import get_account_id_from_bech32
from wallet.services.fund_pull_pre_approval import Role
from wallet.services.validation_tool import request_funds_pull_pre_approval_from_another
from wallet.storage import db_session, funds_pull_pre_approval_command as fppa_storage
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser

SOME_ADDRESS_BECH32 = "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc"
SOME_DESCRIPTION = "Children of the future watching empires fall"


class TestRequestFundsPullPreApprovalFromAnother:
    def test_all_fields_set(self):
        user = OneUser.run(db_session)

        expected_scope = offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=12345,
            max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                unit=offchain.TimeUnit.month,
                value=3,
                max_amount=offchain.CurrencyObject(
                    amount=333444555,
                    currency="XUS",
                ),
            ),
            max_transaction_amount=offchain.CurrencyObject(
                amount=111222,
                currency="XUS",
            ),
        )

        fppa_id = request_funds_pull_pre_approval_from_another(
            account_id=user.account_id,
            payer_address=SOME_ADDRESS_BECH32,
            description=SOME_DESCRIPTION,
            scope=expected_scope,
        )

        db_fppa = fppa_storage.get_command_by_id(fppa_id)

        assert db_fppa is not None

        # I should be the payee
        assert get_account_id_from_bech32(db_fppa.biller_address) == user.account_id
        assert db_fppa.role == Role.PAYEE

        assert db_fppa.funds_pull_pre_approval_id == fppa_id
        assert db_fppa.account_id == user.account_id
        assert db_fppa.address == SOME_ADDRESS_BECH32
        assert db_fppa.description == SOME_DESCRIPTION
        assert db_fppa.status == offchain.FundPullPreApprovalStatus.pending

        assert db_fppa.funds_pull_pre_approval_type == expected_scope.type
        assert db_fppa.expiration_timestamp == expected_scope.expiration_timestamp

        assert (
            db_fppa.max_transaction_amount
            == expected_scope.max_transaction_amount.amount
        )
        assert (
            db_fppa.max_transaction_amount_currency
            == expected_scope.max_transaction_amount.currency
        )

        assert db_fppa.max_cumulative_unit == expected_scope.max_cumulative_amount.unit
        assert (
            db_fppa.max_cumulative_unit_value
            == expected_scope.max_cumulative_amount.value
        )
        assert (
            db_fppa.max_cumulative_amount
            == expected_scope.max_cumulative_amount.max_amount.amount
        )
        assert (
            db_fppa.max_cumulative_amount_currency
            == expected_scope.max_cumulative_amount.max_amount.currency
        )

    def test_only_required_fields(self):
        user = OneUser.run(db_session)

        expected_scope = offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=12345,
        )

        fppa_id = request_funds_pull_pre_approval_from_another(
            account_id=user.account_id,
            payer_address=SOME_ADDRESS_BECH32,
            scope=expected_scope,
        )

        db_fppa = fppa_storage.get_command_by_id(fppa_id)

        assert db_fppa is not None

        # I should be the payee
        assert get_account_id_from_bech32(db_fppa.biller_address) == user.account_id
        assert db_fppa.role == Role.PAYEE

        assert db_fppa.funds_pull_pre_approval_id == fppa_id
        assert db_fppa.account_id == user.account_id
        assert db_fppa.address == SOME_ADDRESS_BECH32
        assert db_fppa.description is None
        assert db_fppa.status == offchain.FundPullPreApprovalStatus.pending

        assert db_fppa.funds_pull_pre_approval_type == expected_scope.type
        assert db_fppa.expiration_timestamp == expected_scope.expiration_timestamp

        assert db_fppa.max_transaction_amount is None
        assert db_fppa.max_transaction_amount_currency is None

        assert db_fppa.max_cumulative_unit is None
        assert db_fppa.max_cumulative_unit_value is None
        assert db_fppa.max_cumulative_amount is None
        assert db_fppa.max_cumulative_amount_currency is None
