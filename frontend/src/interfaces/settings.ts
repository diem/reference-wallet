// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, LibraCurrency } from "./currencies";
import { PaymentMethod, User } from "./user";
import { Account, LibraCurrencyBalance } from "./account";

export interface LibraCurrencySettings {
  name: string;
  symbol: LibraCurrency;
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
  balances: LibraCurrencyBalance[];
  userCount: number;
}

export interface AppSettings {
  network: "testnet" | "mainnet";
  currencies: {
    [key in LibraCurrency]: LibraCurrencySettings;
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
