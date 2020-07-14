# pyre-ignore-all-errors[6]

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from libra_utils.custody import Custody
from libra_utils.libra import (
    get_network_supported_currencies,
    mint_and_wait,
    gen_subaddr,
    decode_full_addr,
)
from libra_utils.types.liquidity.currency import CurrencyPairs, CurrencyPair
from libra_utils.types.liquidity.errors import TradeError
from libra_utils.types.liquidity.lp import LPDetails
from libra_utils.types.liquidity.quote import QuoteData, QuoteId, Rate
from libra_utils.types.liquidity.settlement import DebtData, DebtId
from libra_utils.types.liquidity.trade import Direction, TradeId, TradeData
from libra_utils.vasp import Vasp
from . import storage
from .fx import get_rate
from .storage import (
    create_quote,
    create_trade,
    find_trade,
    find_quote,
    create_new_settlement,
    get_all_unsettled_debts,
    settle_debt,
)

LP_IBAN_ADDRESS = "US89 3704 0044 0532 0130 00"
TBD = ""


class LiquidityProvider(Vasp):
    def __init__(self):
        liquidity_custody_account_name = os.getenv(
            "LIQUIDITY_CUSTODY_ACCOUNT_NAME", "liquidity"
        )
        super().__init__(liquidity_custody_account_name)

    @classmethod
    def init_lp(cls):
        Custody.init()
        storage.configure_storage()
        storage.create_storage()
        lp = LiquidityProvider()
        lp.setup_blockchain()
        amount = 1_000_000 * 100_000_000

        for currency in get_network_supported_currencies():
            mint_and_wait(lp.vasp_auth_key, amount, currency.code)

    def lp_details(self) -> LPDetails:
        """
        Liquidity provider details including:
          - LP settlement libra blockchain address
          - LP settlement bank account ISBN
          - Supported Currency pairs
        """
        return LPDetails(
            sub_address=gen_subaddr(),
            vasp=self.vasp_address,
            IBAN_number=LP_IBAN_ADDRESS,
        )

    @staticmethod
    def get_quote(pair: CurrencyPair, amount: int) -> QuoteData:
        """
        Get a buy & sell quote for the given currency pair and amount.
        i.e LibraUsd/USD will return the rate that you BUY / SELL
        1 LibraUsd in exchange for USD at some conversion rate.
        :param pair:
        :param amount:
        :return: quote with buy & sell
        """
        storage_quote = create_quote(
            currency_pair=CurrencyPairs.from_pair(pair),
            rate=get_rate(currency_pair=pair).rate,
            amount=amount,
            expires_at=datetime.now() + timedelta(minutes=10),
        )
        return QuoteData(
            quote_id=QuoteId(uuid.UUID(storage_quote.id)),
            rate=Rate(storage_quote.currency_pair.value, storage_quote.rate),
            expires_at=storage_quote.expires_at,
            amount=storage_quote.amount,
        )

    def trade_and_execute(
        self,
        quote_id: QuoteId,
        direction: Direction,
        libra_bech32_deposit_address: Optional[str] = None,
        tx_version: Optional[int] = None,
    ) -> TradeId:
        """
        For simplicity trade and execute steps embodied into one action.
        On Trade LP will update it's internal ledger with new state of
        balances according to the wallet trade request; i.e For buy trade
        of 1 LibraUsd for 1 Usd wallet balance on LP side will update
        wallet balance to be+1 LibraUSD -1 USD.

        On execution of such trade +1 LibraUSD will be transferred to
        libra_deposit_address so new balance on LP side is now 0 LibraUSD
        -1 USD. Fiat debt is settled in a separate call
        :param quote_id:
        :param direction: BUY / SELL
        :param libra_bech32_deposit_address: Your Libra wallet address for the deposit
        :param tx_version: Transaction version for the deposit you made
                           into LP Libra wallet address; i.e for a buy
                           trade of LibraUSD/Libra you will have to send
                           Libra to the LP deposit address you obtained
                           from lp_details() call
        :return:
        """
        quote = find_quote(quote_id)
        trade = create_trade(direction, quote_id)

        if Direction[trade.direction] == Direction.Buy:
            self.__trade_and_execute_buy(
                quote=quote,
                trade=trade,
                libra_deposit_address=libra_bech32_deposit_address,
            )
        elif Direction[trade.direction] == Direction.Sell:
            self.__trade_and_execute_sell(trade, tx_version)
        else:
            raise AssertionError("Trade direction have to be either Buy or Sell.")

        return TradeId(uuid.UUID(trade.id))

    def __trade_and_execute_buy(self, quote, trade, libra_deposit_address):
        if not libra_deposit_address:
            raise TradeError("Can't execute trade without a deposit address")

        receiver_vasp, receiver_subaddress = decode_full_addr(libra_deposit_address)

        tx_version, tx_sequence = self.send_transaction(
            currency=quote.currency_pair.value.base,
            amount=quote.amount,
            dest_vasp_address=receiver_vasp,
            dest_sub_address=receiver_subaddress,
        )
        trade.executed(tx_version)

    @staticmethod
    def __trade_and_execute_sell(trade, tx_version):
        # Here liquidity provider will validate tx_version supplied by
        # the user match the trade currency and amount.
        trade.executed(tx_version)

    @staticmethod
    def trade_info(trade_id: TradeId) -> TradeData:
        """
        Returns trade execution status for a given trade.
        :param trade_id:
        :return:
        """
        trade = find_trade(trade_id)

        return TradeData(
            trade_id=TradeId(uuid.UUID(trade.id)),
            direction=trade.direction,
            pair=trade.quote.currency_pair.value,
            amount=trade.quote.amount,
            quote=QuoteData(
                quote_id=QuoteId(uuid.UUID(trade.quote.id)),
                rate=Rate(trade.quote.currency_pair.value, trade.quote.rate),
                expires_at=trade.quote.expires_at,
                amount=trade.quote.amount,
            ),
            status=trade.status,
            tx_version=trade.tx_version,
        )

    @staticmethod
    def get_debt() -> List[DebtData]:
        """
        Start a Fiat settlement process.
        :return:
        """
        create_new_settlement()
        unsettled = get_all_unsettled_debts()
        return [
            DebtData(debt_id=DebtId(uuid.UUID(debt.id)), currency=debt.currency, amount=debt.amount)
            for debt in unsettled
        ]

    @staticmethod
    def settle(debt_id: DebtId, settlement_confirmation: str):
        """
        Confirm debt payment.
        """
        settle_debt(debt_id, settlement_confirmation)
