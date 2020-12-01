// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { libraToHumanFriendly } from "./amount-precision";
import { LibraCurrencyBalance } from "../interfaces/account";
import { FiatCurrency, LibraCurrency } from "../interfaces/currencies";
import { FiatCurrencySettings, LibraCurrencySettings } from "../interfaces/settings";
import { PaymentMethod } from "../interfaces/user";
import { TransactionDirection } from "../interfaces/transaction";

export function libraCurrenciesWithBalanceOptions(
  currencies: { [key in LibraCurrency]: LibraCurrencySettings },
  balances: LibraCurrencyBalance[]
): { [key in LibraCurrency]?: string } {
  return balances.reduce((options, balance) => {
    const currency = currencies[balance.currency];
    const balanceAmount = libraToHumanFriendly(balance.balance, true);
    options[balance.currency] = `${currency.name} (${balanceAmount} ${currency.sign} available)`;
    return options;
  }, {});
}

export function libraCurrenciesOptions(
  libraCurrencies: { [key in LibraCurrency]: LibraCurrencySettings }
): { [key in LibraCurrency]?: string } {
  return Object.keys(libraCurrencies).reduce((currencies, libra) => {
    const currency = libraCurrencies[libra];
    currencies[libra] = currency.name;
    return currencies;
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
    libra_amount_desc: "Highest Amount",
    fiat_amount_desc: "Highest Fiat Amount",
    libra_amount_asc: "Lowest Amount",
    fiat_amount_asc: "Lowest Fiat Amount",
  };
}
