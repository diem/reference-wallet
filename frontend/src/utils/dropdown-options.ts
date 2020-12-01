// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { diemAmountToHumanFriendly } from "./amount-precision";
import { CurrencyBalance } from "../interfaces/account";
import { Currency, FiatCurrency } from "../interfaces/currencies";
import { CurrencySettings, FiatCurrencySettings } from "../interfaces/settings";
import { PaymentMethod } from "../interfaces/user";
import { TransactionDirection } from "../interfaces/transaction";

export function currenciesWithBalanceOptions(
  currencies: { [key in Currency]: CurrencySettings },
  balances: CurrencyBalance[]
): { [key in Currency]?: string } {
  return balances.reduce((options, balance) => {
    const currency = currencies[balance.currency];
    const balanceAmount = diemAmountToHumanFriendly(balance.balance, true);
    options[balance.currency] = `${currency.name} (${balanceAmount} ${currency.sign} available)`;
    return options;
  }, {});
}

export function getCurrenciesOptionsMap(
  currencies: { [key in Currency]: CurrencySettings }
): { [key in Currency]?: string } {
  return Object.keys(currencies).reduce((map, c) => {
    map[c] = currencies[c].name;
    return map;
  }, {});
}

export function fiatCurrenciesOptions(
  fiatCurrencies: { [key in FiatCurrency]: FiatCurrencySettings }
): { [key in FiatCurrency]?: string } {
  return Object.keys(fiatCurrencies).reduce((currencies, fiat) => {
    const currency = fiatCurrencies[fiat];
    currencies[fiat] = currency.symbol;
    return currencies;
  }, {});
}

export function paymentMethodOptions(paymentMethods: PaymentMethod[]): { [key: number]: string } {
  return paymentMethods.reduce((paymentMethods, paymentMethod) => {
    paymentMethods[paymentMethod.id] = paymentMethod.name;
    return paymentMethods;
  }, {});
}

export function transactionDirectionsOptions(): { [key in TransactionDirection]: string } {
  return {
    received: "Incoming",
    sent: "Outgoing",
  };
}

export function transactionSortingOptions(): { [key: string]: string } {
  return {
    date_asc: "Newest to Oldest",
    date_desc: "Oldest to Newest",
    amount_desc: "Highest Amount",
    fiat_amount_desc: "Highest Fiat Amount",
    amount_asc: "Lowest Amount",
    fiat_amount_asc: "Lowest Fiat Amount",
  };
}
