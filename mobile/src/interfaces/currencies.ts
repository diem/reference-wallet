// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

export type LibraCurrency = "LBR" | "Coin1" | "Coin2";

export type FiatCurrency = "USD" | "EUR" | "GBP" | "CHF" | "CAD" | "AUD" | "NZD" | "JPY";

export type LibraCurrenciesSettings = {
  [key in LibraCurrency]: {
    name: string;
    symbol: LibraCurrency;
    sign: string;
  };
};

export type FiatCurrenciesSettings = {
  [key in FiatCurrency]: {
    symbol: FiatCurrency;
    sign: string;
  };
};

export type Rates = {
  [key in LibraCurrency]: {
    [key in FiatCurrency | LibraCurrency]: number;
  };
};
