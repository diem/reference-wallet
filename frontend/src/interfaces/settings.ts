// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, Currency } from "./currencies";
import { PaymentMethod, User } from "./user";
import { Account, CurrencyBalance } from "./account";

export interface CurrencySettings {
  name: string;
  symbol: Currency;
  sign: string;
  rates: {
    [key in FiatCurrency]: number;
  };
}

export interface FiatCurrencySettings {
  symbol: FiatCurrency;
  sign: string;
}

export interface WalletTotals {
  balances: CurrencyBalance[];
  userCount: number;
}

export interface AppSettings {
  network: string;
  currencies: {
    [key in Currency]: CurrencySettings;
  };
  fiatCurrencies: {
    [key in FiatCurrency]: FiatCurrencySettings;
  };
  user?: User;
  account?: Account;
  language?: string;
  defaultFiatCurrencyCode?: FiatCurrency;
  paymentMethods?: PaymentMethod[];
  walletTotals: WalletTotals;
}
