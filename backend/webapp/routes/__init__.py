# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from .account import account, AccountRoutes
from .admin import admin, AdminRoutes
from .cico import cico, CicoRoutes
from .system import system, SystemRoutes
from .user import user, UserRoutes


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
        rule="/user", view_func=UserRoutes.GetUser.as_view("get_user"), methods=["GET"],
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


account_routes()
cico_routes()
admin_routes()
user_routes()
system_routes()
