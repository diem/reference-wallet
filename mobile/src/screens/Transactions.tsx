// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { userContext, withUserContext } from "../contexts/user";
import { accountContext, withAccountContext } from "../contexts/account";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { ratesContext, withRatesContext } from "../contexts/rates";
import BackendClient from "../services/backendClient";
import SessionStorage from "../services/sessionStorage";
import { Transaction, TransactionDirection } from "../interfaces/transaction";
import TransactionsList from "../components/TransactionsList";
import { BackendError } from "../services/errors";
import httpStatus from "http-status-codes";
import { DiemCurrency } from "../interfaces/currencies";
import SelectDropdown from "../components/Select";
import {
  diemCurrenciesOptions,
  transactionDirectionsOptions,
  transactionSortingOptions,
} from "../utils/dropdown-options";
import ExampleSectionWarning from "../components/ExampleSectionWarning";
import TestnetWarning from "../components/TestnetWarning";

const REFRESH_TRANSACTIONS_INTERVAL = 3000;

function Transactions({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("layout");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const [diemCurrency, setDiemCurrency] = useState<DiemCurrency>();
  const [direction, setDirection] = useState<TransactionDirection>();
  const [sorting, setSorting] = useState<string>("date_desc");

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
          await new BackendClient(token).getTransactions(diemCurrency, direction, sorting)
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
  }, [diemCurrency, direction, sorting]);

  const [transactions, setTransactions] = useState<Transaction[]>([]);

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            <TestnetWarning />

            {user && rates && account ? (
              <>
                <View style={theme.SmallContainer}>
                  <Text style={theme.SubTitle}>{t("all_transactions")}</Text>

                  <View
                    style={StyleSheet.flatten([theme.Section, theme.ButtonsGroup.containerStyle])}
                  >
                    <View style={theme.ButtonsGroup.buttonStyle}>
                      <SelectDropdown
                        label={t("all_currencies")}
                        value={diemCurrency}
                        options={diemCurrenciesOptions()}
                        onChange={(val) => setDiemCurrency(val)}
                      />
                    </View>

                    <View style={theme.ButtonsGroup.buttonStyle}>
                      <SelectDropdown
                        label={t("all_transactions")}
                        value={direction}
                        options={transactionDirectionsOptions()}
                        onChange={(val) => setDirection(val)}
                      />
                    </View>

                    <View style={theme.ButtonsGroup.buttonStyle}>
                      <SelectDropdown
                        label={t("all_sorts")}
                        value={sorting}
                        options={transactionSortingOptions()}
                        onChange={(val) => setSorting(val as string)}
                      />
                    </View>
                  </View>
                </View>

                {!!transactions.length && (
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

export default withRatesContext(withAccountContext(withUserContext(Transactions)));
