// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { PaymentMethod } from "../interfaces/user";
import { FiatCurrency, LibraCurrency } from "../interfaces/currencies";
import { LibraCurrencyBalance } from "../interfaces/account";
import { libraToHumanFriendly } from "./amount-precision";
import { fiatCurrencies, libraCurrencies } from "../currencies";
import { TransactionDirection } from "../interfaces/transaction";
import { Languages } from "../i18n";

type LibraCurrenciesWithBalanceOptions = { [key in LibraCurrency]?: string };

export function libraCurrenciesWithBalanceOptions(
  balances: LibraCurrencyBalance[]
): LibraCurrenciesWithBalanceOptions {
  return balances.reduce((options, balance) => {
    const currency = libraCurrencies[balance.currency];
    const balanceAmount = libraToHumanFriendly(balance.balance, true);
    options[balance.currency] = `${currency.name} (${balanceAmount} ${currency.sign} available)`;
    return options;
  }, {} as LibraCurrenciesWithBalanceOptions);
}

type LibraCurrencies = { [key in LibraCurrency]: string };

export function libraCurrenciesOptions(): LibraCurrencies {
  return Object.keys(libraCurrencies).reduce((currencies, currency) => {
    const libraCurrency = libraCurrencies[currency as LibraCurrency];
    currencies[currency as LibraCurrency] = libraCurrency.name;
    return currencies;
  }, {} as LibraCurrencies);
}

type FiatCurrenciesOptions = { [key in FiatCurrency]: string };

export function fiatCurrenciesOptions(): FiatCurrenciesOptions {
  return Object.keys(fiatCurrencies).reduce((currencies, fiat) => {
    const currency = fiatCurrencies[fiat as keyof typeof fiatCurrencies];
    currencies[fiat as keyof typeof fiatCurrencies] = currency.symbol;
    return currencies;
  }, {} as FiatCurrenciesOptions);
}

type PaymentMethodOptions = { [key: number]: string };

export function paymentMethodOptions(paymentMethods: PaymentMethod[]): PaymentMethodOptions {
  return paymentMethods.reduce((paymentMethods, paymentMethod) => {
    paymentMethods[paymentMethod.id] = paymentMethod.name;
    return paymentMethods;
  }, {} as PaymentMethodOptions);
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

type LanguagesOptions = { [key: string]: string };

export function languagesOptions(): LanguagesOptions {
  return Languages.reduce((languages, lang) => {
    languages[lang] = lang.toUpperCase();
    return languages;
  }, {} as LanguagesOptions);
}
