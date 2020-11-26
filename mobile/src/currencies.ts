// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrenciesSettings, DiemCurrenciesSettings } from "./interfaces/currencies";

export const diemCurrencies: DiemCurrenciesSettings = {
  XDM: {
    name: "Diem",
    symbol: "XDM",
    sign: "≋XDM",
  },
  Coin1: {
    name: "Coin1",
    symbol: "Coin1",
    sign: "≋Coin1",
  },
  Coin2: {
    name: "Coin2",
    symbol: "Coin2",
    sign: "≋Coin2",
  },
};

export const fiatCurrencies: FiatCurrenciesSettings = {
  USD: {
    symbol: "USD",
    sign: "$",
  },
  EUR: {
    symbol: "EUR",
    sign: "€",
  },
  GBP: {
    symbol: "GBP",
    sign: "£",
  },
  CHF: {
    symbol: "CHF",
    sign: "Fr",
  },
  CAD: {
    symbol: "CAD",
    sign: "$",
  },
  AUD: {
    symbol: "AUD",
    sign: "$",
  },
  NZD: {
    symbol: "NZD",
    sign: "$",
  },
  JPY: {
    symbol: "JPY",
    sign: "¥",
  },
};
