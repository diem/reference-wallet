// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

export type DiemCurrency = "XDM" | "Coin1" | "Coin2";

export type FiatCurrency = "USD" | "EUR" | "GBP" | "CHF" | "CAD" | "AUD" | "NZD" | "JPY";

export type DiemCurrenciesSettings = {
  [key in DiemCurrency]: {
    name: string;
    symbol: DiemCurrency;
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
  [key in DiemCurrency]: {
    [key in FiatCurrency | DiemCurrency]: number;
  };
};
