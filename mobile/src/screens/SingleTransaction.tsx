// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { NavigationComponentProps } from "react-native-navigation";
import { Badge, BadgeProps, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { userContext, withUserContext } from "../contexts/user";
import { accountContext, withAccountContext } from "../contexts/account";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { ratesContext, withRatesContext } from "../contexts/rates";
import BackendClient from "../services/backendClient";
import SessionStorage from "../services/sessionStorage";
import { BackendError } from "../services/errors";
import httpStatus from "http-status-codes";
import { Transaction, TransactionStatus } from "../interfaces/transaction";
import { fiatToHumanFriendly, libraToFloat, libraToHumanFriendly } from "../utils/amount-precision";
import { fiatCurrencies, libraCurrencies } from "../currencies";
import ExplorerLink from "../components/ExplorerLink";

const STATUS_COLORS: { [key in TransactionStatus]: BadgeProps["status"] } = {
  completed: "success",
  pending: "warning",
  canceled: "error",
};

interface SingleTransactionProps {
  transaction: Transaction;
}

function SingleTransaction({
  transaction,
  componentId,
}: SingleTransactionProps & NavigationComponentProps) {
  const { t } = useTranslation("transaction");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

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
  }, []);

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {user && rates && account ? (
              <>
                {(() => {
                  const libraCurrency = libraCurrencies[transaction.currency];
                  const fiatCurrency = fiatCurrencies[user.selected_fiat_currency];
                  const exchangeRate = rates[transaction.currency][user.selected_fiat_currency];

                  return (
                    <View style={theme.Container}>
                      <View style={StyleSheet.flatten([theme.Section, { alignItems: "center" }])}>
                        {transaction.direction == "sent" && (
                          <Text style={theme.Title}>{t("sent")}</Text>
                        )}
                        {transaction.direction == "received" && (
                          <Text style={theme.Title}>{t("received")}</Text>
                        )}
                      </View>
                      <View style={StyleSheet.flatten([theme.Section, { alignItems: "center" }])}>
                        <Text style={theme.Title}>
                          {libraToHumanFriendly(transaction.amount, true)} {libraCurrency.sign}
                        </Text>
                        <Text>
                          {t("price")} {fiatCurrency.sign}
                          {fiatToHumanFriendly(
                            libraToFloat(transaction.amount) * exchangeRate,
                            true
                          )}{" "}
                          {fiatCurrency.symbol}
                        </Text>
                      </View>
                      <View style={theme.Section}>
                        <Text>{t("date")}</Text>
                        <Text style={{ color: "#000000" }}>
                          {new Date(transaction.timestamp).toLocaleString()}
                        </Text>
                      </View>
                      {transaction.direction === "sent" && (
                        <View style={theme.Section}>
                          <Text>{t("sent_to")}</Text>
                          <Text style={{ color: "#000000" }}>
                            {transaction.destination.full_addr}
                          </Text>
                        </View>
                      )}
                      {transaction.direction === "received" && (
                        <View style={theme.Section}>
                          <Text>{t("sent_from")}</Text>
                          <Text style={{ color: "#000000" }}>{transaction.source.full_addr}</Text>
                        </View>
                      )}
                      <View style={theme.Section}>
                        <Text>{t("status")}</Text>
                        <View style={{ flexDirection: "row", alignItems: "center" }}>
                          <Badge status={STATUS_COLORS[transaction.status]} />
                          <Text style={{ color: "#000000" }}> {transaction.status}</Text>
                        </View>
                      </View>

                      {transaction.blockchain_tx && (
                        <View style={theme.Section}>
                          <Text>{t("tx_id")}</Text>
                          <ExplorerLink blockchainTx={transaction.blockchain_tx} />
                        </View>
                      )}
                    </View>
                  );
                })()}
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

export default withRatesContext(withAccountContext(withUserContext(SingleTransaction)));
