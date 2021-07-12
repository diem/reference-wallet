# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from .account import account, AccountRoutes
from .admin import admin, AdminRoutes
from .cico import cico, CicoRoutes
from webapp.routes.offchain.main_offchain import offchain, OffchainMainRoute
from webapp.routes.offchain.funds_pull_pre_approval import (
    funds_pull_pre_approval,
    FundsPullPreApprovalsRoutes,
)
from webapp.routes.offchain.p2m_payment import p2m_payments, P2MPaymentRoutes
from webapp.routes.offchain.p2p_payment import p2p_payments, P2PPaymentRoutes
from .system import system, SystemRoutes
from .user import user, UserRoutes
from .validation_tool import validation_tool, ValidationToolRoutes


def account_routes():
    account.add_url_rule(
        rule="/account",
        view_func=AccountRoutes.AccountInfo.as_view("account_info"),
        methods=["GET"],
    )
    account.add_url_rule(
        rule="/account/transactions",
        view_func=AccountRoutes.GetAllTransactions.as_view("account_transactions"),
        methods=["GET"],
    )
    account.add_url_rule(
        rule="/account/transactions",
        view_func=AccountRoutes.SendTransaction.as_view("send_transaction"),
        methods=["POST"],
    )
    account.add_url_rule(
        rule="/account/transactions/<transaction_id>",
        view_func=AccountRoutes.GetSingleTransaction.as_view(
            "account_transactions_by_id"
        ),
        methods=["GET"],
    )
    account.add_url_rule(
        rule="/account/receiving-addresses",
        view_func=AccountRoutes.GetReceivingAddress.as_view("get_receiving_address"),
        methods=["POST"],
    )


def cico_routes():
    cico.add_url_rule(
        rule="/account/quotes",
        view_func=CicoRoutes.CreateQuoteView.as_view("create_quote"),
        methods=["POST"],
    )
    cico.add_url_rule(
        rule="/account/quotes/<uuid:quote_id>",
        view_func=CicoRoutes.GetQuoteStatusView.as_view("get_quote_status"),
        methods=["GET"],
    )
    cico.add_url_rule(
        rule="/account/quotes/<uuid:quote_id>/actions/execute",
        view_func=CicoRoutes.ExecuteQuoteView.as_view("execute_quote"),
        methods=["POST"],
    )
    cico.add_url_rule(
        rule="/account/rates",
        view_func=CicoRoutes.GetRatesView.as_view("get_rates"),
        methods=["GET"],
    )


def admin_routes():
    admin.add_url_rule(
        rule="/admin/users",
        view_func=AdminRoutes.GetUsersView.as_view("get_users"),
        methods=["GET"],
    )
    admin.add_url_rule(
        rule="/admin/users/count",
        view_func=AdminRoutes.GetWalletUserCountView.as_view("get_user_count"),
        methods=["GET"],
    )
    admin.add_url_rule(
        rule="/admin/users",
        view_func=AdminRoutes.CreateUserView.as_view("create_user"),
        methods=["POST"],
    )
    admin.add_url_rule(
        rule="/admin/users/<int:user_id>",
        view_func=AdminRoutes.BlockUserView.as_view("block_user"),
        methods=["PUT"],
    )
    admin.add_url_rule(
        rule="/admin/settlement",
        view_func=AdminRoutes.GetSettlementView.as_view("get_settlement"),
        methods=["GET"],
    )
    admin.add_url_rule(
        rule="/admin/settlement/<uuid:debt_id>",
        view_func=AdminRoutes.SettleDebtView.as_view("settle_debt"),
        methods=["PUT"],
    )
    admin.add_url_rule(
        rule="/admin/total-balances",
        view_func=AdminRoutes.GetWalletTotalBalancesView.as_view("total_balances"),
        methods=["GET"],
    )


def user_routes():
    user.add_url_rule(
        rule="/user",
        view_func=UserRoutes.GetUser.as_view("get_user"),
        methods=["GET"],
    )
    user.add_url_rule(
        rule="/user",
        view_func=UserRoutes.CreateUser.as_view("create_user"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user",
        view_func=UserRoutes.UpdateUser.as_view("update_user"),
        methods=["PUT"],
    )
    user.add_url_rule(
        rule="/user/actions/signin",
        view_func=UserRoutes.SignIn.as_view("signin"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/actions/signout",
        view_func=UserRoutes.SignOut.as_view("signout"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/actions/refresh",
        view_func=UserRoutes.RefreshToken.as_view("refresh_token"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/actions/forgot_password",
        view_func=UserRoutes.ForgotPassword.as_view("forgot_password"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/actions/reset_password",
        view_func=UserRoutes.ResetPassword.as_view("reset_password"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/payment-methods",
        view_func=UserRoutes.StorePaymentMethod.as_view("store_payment_method"),
        methods=["POST"],
    )
    user.add_url_rule(
        rule="/user/payment-methods",
        view_func=UserRoutes.GetPaymentMethods.as_view("get_user_payment_methods"),
        methods=["GET"],
    )


def system_routes():
    system.add_url_rule(
        rule="/network",
        view_func=SystemRoutes.GetNetworkView.as_view("get_network"),
        methods=["GET"],
    )


def offchain_api_routes():
    # main offchain end point for all incoming requests
    offchain.add_url_rule(
        rule="/offchain/v2/command",
        view_func=OffchainMainRoute.OffchainV2View.as_view("command_response"),
        methods=["POST"],
    )
    # p2p payments end points
    p2p_payments.add_url_rule(
        rule="/offchain/query/payment_command/<reference_id>",
        view_func=P2PPaymentRoutes.GetP2PPayment.as_view("get p2p payments"),
        methods=["GET"],
    )
    p2p_payments.add_url_rule(
        rule="/offchain/query/payment_command",
        view_func=P2PPaymentRoutes.GetAccountP2PPayments.as_view(
            "get account p2p payments"
        ),
        methods=["GET"],
    )
    p2p_payments.add_url_rule(
        rule="/offchain/payment_command",
        view_func=P2PPaymentRoutes.CreateP2PPaymentAsSender.as_view(
            "create p2p payment command"
        ),
        methods=["POST"],
    )
    p2p_payments.add_url_rule(
        rule="/offchain/payment_command/<reference_id>/actions/approve",
        view_func=P2PPaymentRoutes.ApproveP2PPayment.as_view(
            "approve p2p payment command"
        ),
        methods=["POST"],
    )
    p2p_payments.add_url_rule(
        rule="/offchain/payment_command/<reference_id>/actions/reject",
        view_func=P2PPaymentRoutes.RejectP2PPayment.as_view("reject p2p payment"),
        methods=["POST"],
    )
    # funds pull pre approval (consent) end points
    funds_pull_pre_approval.add_url_rule(
        rule="/offchain/funds_pull_pre_approvals",
        view_func=FundsPullPreApprovalsRoutes.GetFundsPullPreApprovals.as_view(
            "get funds pull pre approval"
        ),
        methods=["GET"],
    )
    funds_pull_pre_approval.add_url_rule(
        rule="/offchain/funds_pull_pre_approvals/<funds_pull_pre_approval_id>",
        view_func=FundsPullPreApprovalsRoutes.UpdateFundPullPreApprovalStatus.as_view(
            "approve funds pull pre approval"
        ),
        methods=["PUT"],
    )
    funds_pull_pre_approval.add_url_rule(
        rule="/offchain/funds_pull_pre_approvals",
        view_func=FundsPullPreApprovalsRoutes.CreateAndApprove.as_view(
            "create and approve funds pull pre approval"
        ),
        methods=["POST"],
    )
    # p2m payments end points
    p2m_payments.add_url_rule(
        rule="/offchain/query/payment_details",
        view_func=P2MPaymentRoutes.GetP2MPaymentDetails.as_view(
            "get p2m payment details"
        ),
        methods=["GET"],
    )
    p2m_payments.add_url_rule(
        rule="/offchain/payment/<reference_id>/actions/approve",
        view_func=P2MPaymentRoutes.ApproveP2MPayment.as_view("approve p2m payment"),
        methods=["POST"],
    )
    p2m_payments.add_url_rule(
        rule="/offchain/payment/<reference_id>/actions/reject",
        view_func=P2MPaymentRoutes.RejectP2MPayment.as_view("reject p2m payment"),
        methods=["POST"],
    )
    p2m_payments.add_url_rule(
        rule="/offchain/payment",
        view_func=P2MPaymentRoutes.CreateNewP2MPayment.as_view(
            "create new p2m payment"
        ),
        methods=["POST"],
    )


def validation_tool_routes():
    validation_tool.add_url_rule(
        rule="/validation/funds_pull_pre_approvals",
        view_func=ValidationToolRoutes.CreateFundsPullPreApprovalRequest.as_view(
            "create funds pull pre approval request"
        ),
        methods=["POST"],
    )
    validation_tool.add_url_rule(
        rule="/validation/payment_info/<action>",
        view_func=ValidationToolRoutes.PreparePaymentAsReceiver.as_view(
            "prepare p2m payment as receiver"
        ),
        methods=["POST"],
    )


account_routes()
cico_routes()
admin_routes()
user_routes()
system_routes()
offchain_api_routes()
validation_tool_routes()
