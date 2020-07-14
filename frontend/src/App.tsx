// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter, Redirect, Switch } from "react-router-dom";
import httpStatus from "http-status-codes";
import Header from "./components/Header";
import Feedback from "./components/Feedback";
import Home from "./pages/Home";
import Wallet from "./pages/Wallet";
import Transactions from "./pages/Transactions";
import Signin from "./pages/Signin";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Verify from "./pages/Verify";
import Settings from "./pages/Settings";
import { AppSettings } from "./interfaces/settings";
import { settingsContext } from "./contexts/app";
import SessionStorage from "./services/sessionStorage";
import BackendClient from "./services/backendClient";
import { BackendError } from "./services/errors";
import { LoggedInRoute, LoggedOutRoute } from "./utils/auth-routes";
import { libraToFloat } from "./utils/amount-precision";
import i18next from "./i18n";
import "./assets/scss/libra-reference-wallet.scss";
import Admins from "./pages/admin/Admins";
import Users from "./pages/admin/Users";
import Liquidity from "./pages/admin/Liquidity";

const REFRESH_USER_INTERVAL = 5000;

const App = () => {
  const [settings, setSettings] = useState<AppSettings>({
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
  });

  const settingsRef = useRef<AppSettings>();
  settingsRef.current = settings;

  const RefreshUser = async () => {
    try {
      if (SessionStorage.getAccessToken()) {
        const backendClient = new BackendClient();

        const getTotalBalances = async () => {
          if (settingsRef.current?.user?.is_admin) {
            return backendClient.getWalletTotalBalances();
          }
          return [];
        };

        const getUserCount = async () => {
          if (settingsRef.current?.user?.is_admin) {
            return backendClient.getUsersCount();
          }
          return -1;
        };

        const [user, account, paymentMethods, rates, totalBalances, userCount] = await Promise.all([
          backendClient.getUser(),
          backendClient.getAccount(),
          backendClient.getPaymentMethods(),
          backendClient.getRates(),
          getTotalBalances(),
          getUserCount(),
        ]);

        if (settingsRef.current!.language !== user.selected_language) {
          await i18next.changeLanguage(user.selected_language);
        }

        const currencies = { ...settings.currencies };
        for (const rate of rates) {
          const [libraCurrency, fiatCurrency] = rate.currency_pair.split("_");
          currencies[libraCurrency].rates[fiatCurrency] = rate.price;
        }

        const sortedBalances = account.balances.sort((a, b) => {
          const libraCurrencyA = settings.currencies[a.currency];
          const libraCurrencyB = settings.currencies[b.currency];

          const exchangeRateA = libraCurrencyA.rates[settings.defaultFiatCurrencyCode!];
          const priceA = libraToFloat(a.balance) * exchangeRateA;
          const exchangeRateB = libraCurrencyB.rates[settings.defaultFiatCurrencyCode!];
          const priceB = libraToFloat(b.balance) * exchangeRateB;

          return priceA <= priceB ? 1 : -1;
        });

        setSettings({
          ...settings,
          user: { ...settings.user, ...user },
          account: { balances: sortedBalances },
          language: user.selected_language,
          currencies,
          defaultFiatCurrencyCode: user.selected_fiat_currency,
          paymentMethods,
          walletTotals: { balances: totalBalances, userCount },
        });
      }
    } catch (e) {
      if (e instanceof BackendError) {
        if (e.httpStatus === httpStatus.UNAUTHORIZED) {
          SessionStorage.removeAccessToken();
          window.location.href = "/";
        }
      }
    }

    setTimeout(RefreshUser, REFRESH_USER_INTERVAL);
  };

  useEffect(() => {
    RefreshUser();
  }, []);

  return (
    <settingsContext.Provider value={[settings, setSettings]}>
      <BrowserRouter>
        <Header />
        <main>
          <Switch>
            <LoggedInRoute path="/" exact component={Home} />
            <LoggedInRoute path="/wallet/:currency" exact component={Wallet} />
            <LoggedInRoute path="/transactions" exact component={Transactions} />
            <LoggedInRoute path="/verify" exact component={Verify} />
            <LoggedInRoute path="/settings" exact component={Settings} />

            <LoggedInRoute path="/admin/users" exact component={Users} />
            <LoggedInRoute path="/admin/admins" exact component={Admins} />
            <LoggedInRoute path="/admin/liquidity" exact component={Liquidity} />

            <LoggedOutRoute path="/login" exact component={Signin} />
            <LoggedOutRoute path="/signup" exact component={Signup} />
            <LoggedOutRoute path="/forgot-password" exact component={ForgotPassword} />
            <LoggedOutRoute path="/reset-password" exact component={ResetPassword} />
            <Redirect to="/" />
          </Switch>
        </main>
        <Feedback />
      </BrowserRouter>
    </settingsContext.Provider>
  );
};

export default App;
