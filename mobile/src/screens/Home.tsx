// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Linking, StyleSheet, TouchableOpacity, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { RegistrationStatus } from "../interfaces/user";
import { userContext, withUserContext } from "../contexts/user";
import { accountContext, withAccountContext } from "../contexts/account";
import ScreenLayout from "../components/ScreenLayout";
import VerifyingMessage from "../components/VerifyingMessage";
import { appTheme } from "../styles";
import { ratesContext, withRatesContext } from "../contexts/rates";
import TotalBalance from "../components/TotalBalance";
import BackendClient from "../services/backendClient";
import BalancesList from "../components/BalancesList";
import SessionStorage from "../services/sessionStorage";
import { Transaction } from "../interfaces/transaction";
import TransactionsList from "../components/TransactionsList";
import { BackendError } from "../services/errors";
import httpStatus from "http-status-codes";
import TestnetWarning from "../components/TestnetWarning";

const REFRESH_TRANSACTIONS_INTERVAL = 3000;

function Home({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("layout");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  useEffect(() => {
    const userVerificationRequired =
      user && user.registration_status === RegistrationStatus.Registered;

    if (userVerificationRequired) {
      Navigation.setStackRoot(componentId, {
        component: {
          name: "Verify",
        },
      });
    }
  }, [user]);

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
        setTransactions(
          await new BackendClient(token).getTransactions(undefined, undefined, undefined, 10)
        );

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

  useEffect(() => {
    function handleDeepLink({ url }: { url: string }) {
      Navigation.push(componentId, {
        component: {
          name: "Send",
          passProps: {
            addressWithIntents: url,
          },
        },
      });
    }
    Linking.addEventListener("url", handleDeepLink);

    return () => {
      Linking.removeEventListener("url", handleDeepLink);
    };
  });

  return (
    <ScreenLayout hideHeaderBack={true} showLegalDisclaimer={true} componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            <TestnetWarning />

            {user && rates && account ? (
              user.registration_status === RegistrationStatus.Pending ? (
                <VerifyingMessage />
              ) : (
                <>
                  <View style={{ ...theme.Container, alignItems: "center" }}>
                    <Text style={theme.SubTitle}>
                      {user.first_name} {user.last_name}
                    </Text>
                  </View>

                  <View style={StyleSheet.flatten([theme.Container, theme.Section])}>
                    <TotalBalance
                      balances={account.balances}
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

                  <View style={theme.SmallContainer}>
                    <Text style={theme.SubTitle}>{t("balances")}</Text>
                  </View>
                  <View style={theme.Section}>
                    <BalancesList
                      balances={account.balances}
                      fiatCurrencyCode={user.selected_fiat_currency}
                      rates={rates}
                      onSelect={(currencyCode) => {
                        Navigation.push(componentId, {
                          component: {
                            name: "Account",
                            passProps: {
                              currencyCode,
                            },
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
                          bottom={
                            <TouchableOpacity
                              style={{ alignItems: "center" }}
                              onPress={() => {
                                Navigation.push(componentId, {
                                  component: {
                                    name: "Transactions",
                                  },
                                });
                              }}
                            >
                              <Text style={{ color: "#000000" }}>{t("all_transactions")}</Text>
                            </TouchableOpacity>
                          }
                        />
                      </View>
                    </>
                  )}
                </>
              )
            ) : (
              <ActivityIndicator size="large" />
            )}
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withRatesContext(withAccountContext(withUserContext(Home)));
