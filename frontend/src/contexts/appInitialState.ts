import { AppSettings } from "../interfaces/settings";

export const initialState: AppSettings = {
  network: "",
  currencies: {
    Coin1: {
      name: "Coin1",
      symbol: "Coin1",
      sign: "≋Coin1",
      rates: {
        USD: 1,
        EUR: 0.85,
        GBP: 0.8,
        CHF: 1,
        CAD: 1,
        AUD: 1,
        NZD: 1,
        JPY: 1,
      },
    },
  },
  fiatCurrencies: {
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
  },
  user: undefined,
  account: undefined,
  paymentMethods: undefined,
  walletTotals: { balances: [], userCount: -1 },
  language: "en",
  defaultFiatCurrencyCode: "USD",
};
