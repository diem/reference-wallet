// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { userContext, withUserContext } from "../../contexts/user";
import { accountContext, withAccountContext } from "../../contexts/account";
import ScreenLayout from "../../components/ScreenLayout";
import { appTheme } from "../../styles";
import { ratesContext, withRatesContext } from "../../contexts/rates";
import { Quote } from "../../interfaces/cico";
import { paymentMethodsLabels } from "../../interfaces/user";
import { fiatCurrencies, diemCurrencies } from "../../currencies";
import {
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  diemFromFloat,
  diemToHumanFriendly,
} from "../../utils/amount-precision";
import { FiatCurrency, DiemCurrency } from "../../interfaces/currencies";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

interface SendReviewProps {
  diemCurrencyCode: DiemCurrency;
  fiatCurrencyCode: FiatCurrency;
  diemAmount: number;
  diemAddress: string;
}

function SendReview({
  diemCurrencyCode,
  fiatCurrencyCode,
  diemAmount,
  diemAddress,
  componentId,
}: SendReviewProps & NavigationComponentProps) {
  const { t } = useTranslation("send");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  async function handleSubmit() {
    try {
      setSubmitStatus("sending");
      const token = await SessionStorage.getAccessToken();
      const transaction = await new BackendClient(token).createTransaction(
        diemCurrencyCode,
        diemFromFloat(diemAmount),
        diemAddress
      );
      setSubmitStatus("success");
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected Error", e);
      }
    }
  }

  async function goToRoot() {
    await Navigation.popToRoot(componentId);
  }

  async function goBack() {
    await Navigation.pop(componentId);
  }

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {user && account && rates ? (
              <>
                {(() => {
                  const diemCurrency = diemCurrencies[diemCurrencyCode];
                  const fiatCurrency = fiatCurrencies[fiatCurrencyCode];

                  const exchangeRate = rates[diemCurrencyCode][fiatCurrencyCode];

                  return (
                    <View style={theme.Container}>
                      {errorMessage && <ErrorMessage message={errorMessage} />}

                      <View style={theme.Section}>
                        <Text h1>{t("review.title")}</Text>
                        <Text>{t("review.description")}</Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("review.amount")}</Text>
                        <Text style={{ color: "black" }}>
                          {diemAmount} {diemCurrency.sign}
                        </Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("review.price")}</Text>
                        <Text style={{ color: "black" }}>
                          {fiatCurrency.sign}
                          {fiatToHumanFriendly(diemAmount * exchangeRate, true)}{" "}
                          {fiatCurrency.symbol}
                        </Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("review.exchange_rate")}</Text>
                        <Text style={{ color: "black" }}>
                          1 {diemCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)}{" "}
                          {fiatCurrency.symbol}
                        </Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("review.address")}</Text>
                        <Text style={{ color: "black" }}>{diemAddress}</Text>
                      </View>

                      {submitStatus !== "success" && (
                        <>
                          <Button
                            containerStyle={theme.Section}
                            title={t("review.confirm")}
                            disabled={submitStatus === "sending"}
                            onPress={handleSubmit}
                          />
                          <Button
                            type="outline"
                            title={t("review.back")}
                            disabled={submitStatus === "sending"}
                            onPress={goBack}
                          />
                        </>
                      )}
                      {submitStatus === "success" && (
                        <>
                          <Button title={t("review.done")} onPress={goToRoot} />
                        </>
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

export default withRatesContext(withAccountContext(withUserContext(SendReview)));
