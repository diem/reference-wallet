// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { PaymentMethod } from "../interfaces/user";
import { FiatCurrency, DiemCurrency } from "../interfaces/currencies";
import { DiemCurrencyBalance } from "../interfaces/account";
import { diemToHumanFriendly } from "./amount-precision";
import { fiatCurrencies, diemCurrencies } from "../currencies";
import { TransactionDirection } from "../interfaces/transaction";
import { Languages } from "../i18n";

type DiemCurrenciesWithBalanceOptions = { [key in DiemCurrency]?: string };

export function diemCurrenciesWithBalanceOptions(
  balances: DiemCurrencyBalance[]
): DiemCurrenciesWithBalanceOptions {
  return balances.reduce((options, balance) => {
    const currency = diemCurrencies[balance.currency];
    const balanceAmount = diemToHumanFriendly(balance.balance, true);
    options[balance.currency] = `${currency.name} (${balanceAmount} ${currency.sign} available)`;
    return options;
  }, {} as DiemCurrenciesWithBalanceOptions);
}

type DiemCurrencies = { [key in DiemCurrency]: string };

export function diemCurrenciesOptions(): DiemCurrencies {
  return Object.keys(diemCurrencies).reduce((currencies, currency) => {
    const diemCurrency = diemCurrencies[currency as DiemCurrency];
    currencies[currency as DiemCurrency] = diemCurrency.name;
    return currencies;
  }, {} as DiemCurrencies);
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
    diem_amount_desc: "Highest Amount",
    fiat_amount_desc: "Highest Fiat Amount",
    diem_amount_asc: "Lowest Amount",
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
