import { AppSettings } from "../interfaces/settings";

export const initialState: AppSettings = {
  network: "testnet",
  currencies: {
    LBR: {
      name: "Libra",
      symbol: "LBR",
      sign: "≋LBR",
      rates: {
        USD: 1.1,
        EUR: 0.95,
        GBP: 0.9,
        CHF: 1,
        CAD: 1,
        AUD: 1,
        NZD: 1,
        JPY: 1,
      },
    },
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
    Coin2: {
      name: "Coin2",
      symbol: "Coin2",
      sign: "≋Coin2",
      rates: {
        USD: 1.1,
        EUR: 1,
        GBP: 0.85,
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
