// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { ActivityIndicator, Clipboard, StyleSheet, View } from "react-native";
import { NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { DiemCurrency } from "../interfaces/currencies";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import SelectDropdown from "../components/Select";
import { diemCurrenciesWithBalanceOptions } from "../utils/dropdown-options";
import { accountContext, withAccountContext } from "../contexts/account";
import QRCode from "react-native-qrcode-svg";
import ErrorMessage from "../components/Messages/ErrorMessage";
import SessionStorage from "../services/sessionStorage";

export const LIBRA_ADDR_PROTOCOL_PREFIX = "diem://";

const Logo = require("../assets/logo.png");

interface ReceiveProps {
  currency?: DiemCurrency;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function Receive({ currency, componentId }: ReceiveProps & NavigationComponentProps) {
  const { t } = useTranslation("receive");

  const account = useContext(accountContext);

  const [selectedCurrency, setSelectedCurrency] = useState<DiemCurrency | undefined>(currency);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");
  const [errorMessage, setErrorMessage] = useState<string>();
  const [receivingAddress, setReceivingAddress] = useState<string>();
  const [copied, setCopied] = useState<boolean>(false);

  const addressWithIntents =
    `${LIBRA_ADDR_PROTOCOL_PREFIX}${receivingAddress}` +
    (selectedCurrency ? `?c=${selectedCurrency}` : "");

  useEffect(() => {
    async function fetchReceivingAddress() {
      try {
        setErrorMessage(undefined);
        setSubmitStatus("sending");
        const token = await SessionStorage.getAccessToken();
        setReceivingAddress(await new BackendClient(token).createReceivingAddress(currency));
        setSubmitStatus("success");
      } catch (e) {
        setSubmitStatus("fail");
        if (e instanceof BackendError) {
          setErrorMessage(e.message);
        } else {
          setErrorMessage("Internal Error");
          console.error("Unexpected error", e);
        }
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    fetchReceivingAddress();
  }, []);

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {account ? (
              <View style={theme.Container}>
                {errorMessage && <ErrorMessage message={errorMessage} />}

                <Text style={StyleSheet.flatten([theme.Title, theme.Section])}>
                  {t("headline")}
                </Text>

                <View style={theme.Section}>
                  <Text>{t("currency_label")}</Text>
                  <SelectDropdown
                    label={t("currency")}
                    value={selectedCurrency}
                    options={diemCurrenciesWithBalanceOptions(account.balances)}
                    onChange={(val) => setSelectedCurrency(val)}
                  />
                </View>

                <View style={theme.Section}>
                  <Text>{t("text")}</Text>
                </View>

                <View style={StyleSheet.flatten([theme.Section, { alignItems: "center" }])}>
                  <QRCode
                    value={receivingAddress}
                    size={200}
                    logo={Logo}
                    logoBackgroundColor="white"
                  />
                </View>
                <Text
                  style={StyleSheet.flatten([
                    theme.Section,
                    { textAlign: "center", fontWeight: "bold", fontSize: 12 },
                  ])}
                >
                  {addressWithIntents}
                </Text>
                <Button
                  title={t("copy")}
                  onPress={() => {
                    Clipboard.setString(addressWithIntents);
                  }}
                />
              </View>
            ) : (
              <ActivityIndicator size="large" />
            )}
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withAccountContext(Receive);
