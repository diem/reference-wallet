// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter, Redirect, Switch } from "react-router-dom";
import httpStatus from "http-status-codes";
import Header from "./components/Header";
import Feedback from "./components/Feedback";
import Home from "./pages/Home";
import Account from "./pages/Account";
import Transactions from "./pages/Transactions";
import Signin from "./pages/Signin";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Verify from "./pages/Verify";
import Settings from "./pages/Settings";
import AdminHome from "./pages/admin/Home";
import Admins from "./pages/admin/Admins";
import Users from "./pages/admin/Users";
import Liquidity from "./pages/admin/Liquidity";
import { AppSettings } from "./interfaces/settings";
import { settingsContext } from "./contexts/app";
import { initialState } from "./contexts/appInitialState";
import SessionStorage from "./services/sessionStorage";
import BackendClient from "./services/backendClient";
import { BackendError } from "./services/errors";
import { LoggedInRoute, LoggedOutRoute } from "./utils/auth-routes";
import { diemAmountToFloat } from "./utils/amount-precision";
import i18next from "./i18n";
import "./assets/scss/main.scss";
import LegalDisclaimer from "./components/LegalDisclaimer";

const REFRESH_USER_INTERVAL = 5000;

const App = () => {
  const [settings, setSettings] = useState<AppSettings>(initialState);

  const settingsRef = useRef<AppSettings>();
  settingsRef.current = settings;

  useEffect(() => {
    const refreshUser = async () => {
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

          const [
            chain,
            user,
            account,
            paymentMethods,
            rates,
            totalBalances,
            userCount,
          ] = await Promise.all([
            backendClient.getChain(),
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
            const [currency, fiatCurrency] = rate.currency_pair.split("_");
            currencies[currency].rates[fiatCurrency] = rate.price;
          }

          const sortedBalances = account.balances.sort((a, b) => {
            const currencyA = settings.currencies[a.currency];
            const currencyB = settings.currencies[b.currency];

            const exchangeRateA = currencyA.rates[settings.defaultFiatCurrencyCode!];
            const priceA = diemAmountToFloat(a.balance) * exchangeRateA;
            const exchangeRateB = currencyB.rates[settings.defaultFiatCurrencyCode!];
            const priceB = diemAmountToFloat(b.balance) * exchangeRateB;

            return priceA <= priceB ? 1 : -1;
          });

          setSettings({
            ...settings,
            network: chain.display_name,
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

      setTimeout(refreshUser, REFRESH_USER_INTERVAL);
    };

    refreshUser();
  }, []);

  const [legalDisclaimer, setLegalDisclaimer] = useState(true);

  return (
    <settingsContext.Provider value={[settings, setSettings]}>
      <BrowserRouter>
        <Header />
        <main>
          {legalDisclaimer ? (
            <LegalDisclaimer onClose={() => setLegalDisclaimer(false)} />
          ) : (
            <Switch>
              {settings.user && settings.user.is_admin ? (
                <LoggedInRoute path="/" exact component={AdminHome} />
              ) : (
                <LoggedInRoute path="/" exact component={Home} />
              )}
              <LoggedInRoute path="/account/:currency" exact component={Account} />
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
          )}
        </main>
        <Feedback />
      </BrowserRouter>
    </settingsContext.Provider>
  );
};

export default App;
