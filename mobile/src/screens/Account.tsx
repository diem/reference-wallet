// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { userContext, withUserContext } from "../contexts/user";
import { accountContext, withAccountContext } from "../contexts/account";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { ratesContext, withRatesContext } from "../contexts/rates";
import BackendClient from "../services/backendClient";
import SessionStorage from "../services/sessionStorage";
import { Transaction } from "../interfaces/transaction";
import TransactionsList from "../components/TransactionsList";
import { BackendError } from "../services/errors";
import httpStatus from "http-status-codes";
import { DiemCurrency } from "../interfaces/currencies";
import { diemCurrencies } from "../currencies";
import CurrencyBalance from "../components/CurrencyBalance";
import TestnetWarning from "../components/TestnetWarning";

const REFRESH_TRANSACTIONS_INTERVAL = 3000;

interface AccountProps {
  currencyCode: DiemCurrency;
}

function Account({ currencyCode, componentId }: AccountProps & NavigationComponentProps) {
  const { t } = useTranslation("layout");

  const diemCurrency = diemCurrencies[currencyCode];

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const fetchTransactionsTimeout = useRef<number>();

  useEffect(() => {
    async function refreshUser() {
      try {
        const token = await SessionStorage.getAccessToken();
        await new BackendClient(token).refreshUser();
      } catch (e) {
        if (e instanceof BackendError && e.httpStatus === httpStatus.UNAUTHORIZED) {
          //
        } else {
          console.error(e);
        }
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();

    async function fetchTransactions() {
      try {
        const token = await SessionStorage.getAccessToken();
        setTransactions(await new BackendClient(token).getTransactions(currencyCode));

        fetchTransactionsTimeout.current = setTimeout(
          fetchTransactions,
          REFRESH_TRANSACTIONS_INTERVAL
        );
      } catch (e) {
        if (e instanceof BackendError && e.httpStatus === httpStatus.UNAUTHORIZED) {
          //
        } else {
          console.error(e);
        }
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    fetchTransactions();

    return () => {
      clearTimeout(fetchTransactionsTimeout.current!);
    };
  }, []);

  const [transactions, setTransactions] = useState<Transaction[]>([]);

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            <TestnetWarning />

            {user && rates && account ? (
              <>
                <View style={{ ...theme.Container, alignItems: "center" }}>
                  <Text style={theme.SubTitle}>{diemCurrency.name} Wallet</Text>
                </View>

                <View style={StyleSheet.flatten([theme.Container, theme.Section])}>
                  <CurrencyBalance
                    balance={account.balances.find((balance) => balance.currency === currencyCode)!}
                    fiatCurrencyCode={user.selected_fiat_currency}
                    rates={rates}
                  />
                </View>

                <View
                  style={StyleSheet.flatten([
                    theme.SmallContainer,
                    theme.Section,
                    theme.ButtonsGroup.containerStyle,
                  ])}
                >
                  <Button
                    type="outline"
                    containerStyle={theme.ButtonsGroup.buttonStyle}
                    title={t("actions.send")}
                    onPress={() => {
                      Navigation.push(componentId, {
                        component: {
                          name: "Send",
                        },
                      });
                    }}
                  />
                  <Button
                    type="outline"
                    containerStyle={theme.ButtonsGroup.buttonStyle}
                    title={t("actions.request")}
                    onPress={() => {
                      Navigation.push(componentId, {
                        component: {
                          name: "Receive",
                        },
                      });
                    }}
                  />
                  <Button
                    type="outline"
                    containerStyle={theme.ButtonsGroup.buttonStyle}
                    title={t("actions.transfer")}
                    onPress={() => {
                      Navigation.push(componentId, {
                        component: {
                          name: "Transfer",
                        },
                      });
                    }}
                  />
                </View>

                {!!transactions.length && (
                  <>
                    <View style={theme.SmallContainer}>
                      <Text style={theme.SubTitle}>{t("transactions")}</Text>
                    </View>
                    <View style={theme.Section}>
                      <TransactionsList
                        transactions={transactions}
                        fiatCurrencyCode={user.selected_fiat_currency}
                        rates={rates}
                        onSelect={(transaction) => {
                          Navigation.push(componentId, {
                            component: {
                              name: "SingleTransaction",
                              passProps: {
                                transaction,
                              },
                            },
                          });
                        }}
                      />
                    </View>
                  </>
                )}
                {!transactions.length && (
                  <View style={theme.Container}>
                    <Text style={{ textAlign: "center" }}>{t("transactions_empty")}</Text>
                  </View>
                )}
              </>
            ) : (
              <ActivityIndicator size="large" />
            )}
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withRatesContext(withAccountContext(withUserContext(Account)));
