# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

# from datetime import datetime
#
# from diem_utils.types.liquidity import Currency, LpClient
# from diem_utils.types.liquidity import (
#     trade_to_debt,
#     Trade,
#     Quote,
#     consolidate_debts,
#     Settlement,
#     Session,
# )
# from diem_utils.types.liquidity import CurrencyPairs
# from diem_utils.types.liquidity import Direction, TradeStatus
#
#
# def make_trade(pair: CurrencyPairs, direction: Direction, amount=1000):
#     # pyre-ignore[28]
#     quote = Quote(
#         currency_pair=pair,
#         rate=2000000,
#         expires_at=datetime(2030, 12, 12),
#         amount=amount,
#     )
#     # pyre-ignore[28]
#     return Trade(direction=direction, quote=quote, status=TradeStatus.Complete)
#
#
# class TestDebtCalculation:
#     def test_diem_fiat_buy(self, liquidity_provider_session):
#         trade = make_trade(CurrencyPairs.Coin1_USD, Direction.Buy)
#         debt = trade_to_debt(trade)
#         assert debt.currency == Currency.USD
#         assert debt.amount == 1000
#
#     def test_diem_fiat_sell(self, liquidity_provider_session):
#         trade = make_trade(CurrencyPairs.Coin1_USD, Direction.Sell)
#         debt = trade_to_debt(trade)
#         assert debt.currency == Currency.USD
#         assert debt.amount == -1000
#
#     def test_fiat_diem_buy(self, liquidity_provider_session):
#         trade = make_trade(CurrencyPairs.EUR_Coin1, Direction.Buy)
#         debt = trade_to_debt(trade)
#         assert debt.currency == Currency.EUR
#         assert debt.amount == -500
#
#     def test_fiat_diem_sell(self, liquidity_provider_session):
#         trade = make_trade(CurrencyPairs.EUR_Coin1, Direction.Sell)
#         debt = trade_to_debt(trade)
#         assert debt.currency == Currency.EUR
#         assert debt.amount == 500
#
#
# def test_consolidate_debts(liquidity_provider_session):
#     settlement = Settlement(id="YUYUAYDEE")
#     trades = [
#         make_trade(CurrencyPairs.Coin1_USD, Direction.Buy, 1),
#         make_trade(CurrencyPairs.Coin1_USD, Direction.Buy, 2),
#         make_trade(CurrencyPairs.Coin1_EUR, Direction.Buy, 3),
#         make_trade(CurrencyPairs.Coin1_USD, Direction.Buy, 4),
#     ]
#     consolidated = sorted(
#         consolidate_debts(settlement, trades), key=lambda x: x.currency
#     )
#
#     assert len(consolidated) == 2
#     assert consolidated[0].currency == Currency.EUR
#     assert consolidated[0].amount == 3
#     assert consolidated[1].currency == Currency.USD
#     assert consolidated[1].amount == 7
#     assert trades[2].debt_id == consolidated[0].id
#     assert len(settlement.debts) == 2
#
#
# def test_settlement(liquidity_provider_session):
#     trade1 = make_trade(CurrencyPairs.Coin1_USD, Direction.Buy)
#     trade2 = make_trade(CurrencyPairs.Coin1_EUR, Direction.Buy)
#     Session.add(trade1)
#     Session.add(trade2)
#     Session.commit()
#
#     debt = sorted(LpClient.get_debt(), key=lambda x: x.currency)
#
#     assert len(debt) == 2
#     assert debt[0].currency == Currency.EUR
#     assert debt[0].amount == 1000
#     assert debt[1].currency == Currency.USD
#     assert debt[1].amount == 1000
#
#     # partial_payment1 = [
#     #     FiatCurrencyDebt(Currency.USD, 1000, "Approved by Sherlock Holmes"),
#     # ]
#     # partial_payment2 = [
#     #     FiatCurrencyDebt(Currency.EUR, 1000, "Approved by Sherlock Holmes"),
#     # ]
#     #
#     # status = Client.settle(settlement_id, partial_payment1)
#     # assert status == SettlementStatus.Partial
#     # assert Client.settlement_summary.settlement_id == settlement_id
#     # assert Client.settlement_summary.status == SettlementStatus.Partial
#     # assert len(Client.settlements_history) == 0
#     #
#     # status = Client.settle(settlement_id, partial_payment2)
#     # assert status == SettlementStatus.Settled
#     # assert Client.settlement_summary.settlement_id != settlement_id
#     # assert Client.settlement_summary.status == SettlementStatus.Pending
#     # assert len(Client.settlement_summary.trades) == 0
#     # assert len(Client.settlements_history) == 1
#     # assert Client.settlements_history[0].settlement_id == settlement_id
