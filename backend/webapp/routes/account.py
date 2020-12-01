# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from typing import Dict

from flask import request, Blueprint
import context

from diem import identifier, utils
from diem_utils.types.currencies import DiemCurrency
from wallet.services import account as account_service
from wallet.services import transaction as transaction_service
from wallet.services.transaction import get_transaction_direction
from wallet.storage import Transaction
from wallet.types import TransactionType, TransactionDirection, TransactionSortOption
from webapp.routes.strict_schema_view import (
    response_definition,
    path_string_param,
    query_str_param,
    body_parameter,
    StrictSchemaView,
    query_int_param,
)
from webapp.schemas import (
    AccountTransactions as AccountTransactionsSchema,
    CreateTransaction,
    Balances as AccountInfoSchema,
    FullAddress as FullAddressSchema,
    Error,
)
from webapp.schemas import Transaction as TransactionSchema

account = Blueprint("account/v1", __name__, url_prefix="/")


class AccountRoutes:
    class AccountView(StrictSchemaView):
        tags = ["Account"]

    class AccountInfo(AccountView):
        summary = "Get an account info"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition(
                "Account information", schema=AccountInfoSchema
            ),
            HTTPStatus.FORBIDDEN: response_definition("Unauthorized", schema=Error),
        }

        def get(self):
            user = self.user
            if user.account is None:  # no account created yet
                return {"balances": []}, HTTPStatus.OK
            account_name = user.account.name

            if not account_service.is_user_allowed_for_account(
                user=user, account_name=account_name
            ):
                return self.respond_with_error(
                    HTTPStatus.FORBIDDEN, "User is forbidden for account"
                )
            balances = account_service.get_account_balance_by_name(
                account_name=account_name
            )

            account_info = {
                "balances": [
                    dict(currency=currency.value, balance=balance)
                    for currency, balance in balances.total.items()
                ]
            }

            return account_info, HTTPStatus.OK

    class GetSingleTransaction(AccountView):
        summary = "Get a single transaction"
        parameters = [
            path_string_param(name="transaction_id", description="transaction id")
        ]
        responses = {
            HTTPStatus.OK: response_definition(
                "A single transaction", schema=TransactionSchema
            ),
            HTTPStatus.NOT_FOUND: response_definition(
                "Transaction not found", schema=Error
            ),
        }

        def get(self, transaction_id: int):
            user = self.user
            account_id = user.account_id
            transaction = transaction_service.get_transaction(
                transaction_id=int(transaction_id)
            )
            if transaction is None or not (
                transaction.source_id == account_id
                or transaction.destination_id == account_id
            ):
                return self.respond_with_error(
                    HTTPStatus.NOT_FOUND,
                    f"Transaction id {transaction_id} was not found.",
                )

            transaction = AccountRoutes.get_transaction_response_object(
                user.account_id, transaction
            )

            return transaction, HTTPStatus.OK

    class GetAllTransactions(AccountView):
        summary = "Get an account transactions"
        parameters = [
            query_str_param(
                name="currency",
                description="currency name",
                required=False,
                allowed_vlaues=list(DiemCurrency.__members__),
            ),
            query_str_param(
                name="direction",
                description="transaction direction",
                required=False,
                allowed_vlaues=["sent", "received"],
            ),
            query_int_param(
                name="limit",
                description="Limin amount of transactions to fetch",
                required=False,
            ),
            query_str_param(
                name="sort",
                description="sort transactions by a requested filter",
                required=False,
                allowed_vlaues=[
                    "date_asc",
                    "date_desc",
                    "diem_amount_desc",
                    "diem_amount_asc",
                    "fiat_amount_desc",
                    "fiat_amount_asc",
                ],
            ),
        ]
        responses = {
            HTTPStatus.OK: response_definition(
                "Account transactions", schema=AccountTransactionsSchema
            ),
        }

        def get(self):
            currency, direction, limit, sort_option = self.get_request_params()

            user = self.user

            if user.account is None:
                return {"transaction_list": []}, HTTPStatus.OK

            account_name = user.account.name

            transactions = account_service.get_account_transactions(
                account_name=account_name,
                currency=currency,
                direction_filter=direction,
                limit=limit,
                sort=sort_option,
            )
            transaction_list = [
                AccountRoutes.get_transaction_response_object(user.account_id, tx)
                for tx in transactions
            ]

            return {"transaction_list": transaction_list}, HTTPStatus.OK

        @staticmethod
        def get_request_params():
            currency = (
                DiemCurrency(request.args["currency"])
                if "currency" in request.args
                else None
            )
            direction = (
                TransactionDirection(request.args["direction"])
                if "direction" in request.args
                else None
            )
            limit = int(request.args["limit"]) if "limit" in request.args else None
            sort_option = (
                TransactionSortOption(request.args["sort"])
                if "sort" in request.args
                else None
            )

            return currency, direction, limit, sort_option

    class SendTransaction(AccountView):
        summary = "Send a transaction"
        parameters = [body_parameter(CreateTransaction)]
        responses = {
            HTTPStatus.OK: response_definition(
                "Created transaction", schema=TransactionSchema
            ),
            HTTPStatus.FAILED_DEPENDENCY: response_definition(
                "Risk check failed", Error
            ),
            HTTPStatus.FORBIDDEN: response_definition(
                "Send to own wallet error", Error
            ),
        }

        def post(self):
            try:
                tx_params = request.json

                user = self.user
                account_id = user.account_id

                currency = DiemCurrency[tx_params["currency"]]
                amount = int(tx_params["amount"])
                recv_address: str = tx_params["receiver_address"]
                dest_address, dest_subaddress = identifier.decode_account(
                    recv_address, context.get().config.diem_address_hrp()
                )

                tx = transaction_service.send_transaction(
                    sender_id=account_id,
                    amount=amount,
                    currency=currency,
                    destination_address=utils.account_address_bytes(dest_address).hex(),
                    destination_subaddress=dest_subaddress.hex(),
                )
                transaction = AccountRoutes.get_transaction_response_object(
                    user.account_id, tx
                )
                return transaction, HTTPStatus.OK
            except transaction_service.RiskCheckError as risk_check_failed_error:
                return self.respond_with_error(
                    HTTPStatus.FAILED_DEPENDENCY, str(risk_check_failed_error)
                )
            except transaction_service.SelfAsDestinationError as send_to_self_error:
                return self.respond_with_error(
                    HTTPStatus.FORBIDDEN, str(send_to_self_error)
                )

    class GetReceivingAddress(AccountView):
        summary = "Get an address for deposit (receive) funds"
        parameters = []
        responses = {
            HTTPStatus.OK: response_definition(
                "Created transaction", schema=FullAddressSchema
            ),
        }

        def post(self):
            user = self.user
            account_name = user.account.name

            full_address = account_service.get_deposit_address(
                account_name=account_name
            )
            return {"address": full_address}, HTTPStatus.OK

    @classmethod
    def get_transaction_response_object(
        cls, account_id: int, transaction: Transaction
    ) -> Dict[str, str]:
        direction = get_transaction_direction(
            account_id=account_id, transaction=transaction
        )

        blockchain_tx = None

        if transaction.type == TransactionType.EXTERNAL:
            blockchain_tx = {
                "amount": transaction.amount,
                "source": transaction.source_address,
                "destination": transaction.destination_address,
                "expirationTime": "",
                "sequenceNumber": transaction.sequence,
                "status": transaction.status,
                "version": transaction.blockchain_version,
            }

        return {
            "id": transaction.id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "direction": direction.value.lower(),
            "status": transaction.status,
            "timestamp": transaction.created_timestamp.isoformat(),
            "source": {
                "vasp_name": transaction.source_address,
                "user_id": transaction.source_subaddress,
                "full_addr": identifier.encode_account(
                    transaction.source_address,
                    transaction.source_subaddress,
                    context.get().config.diem_address_hrp(),
                ),
            },
            "destination": {
                "vasp_name": transaction.destination_address,
                "user_id": transaction.destination_subaddress,
                "full_addr": identifier.encode_account(
                    transaction.destination_address,
                    transaction.destination_subaddress,
                    context.get().config.diem_address_hrp(),
                ),
            },
            "is_internal": transaction.type == TransactionType.INTERNAL,
            "blockchain_tx": blockchain_tx,
        }
