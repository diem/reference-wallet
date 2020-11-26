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
import { diemCurrencies } from "../../currencies";
import { diemToHumanFriendly } from "../../utils/amount-precision";
import { DiemCurrency } from "../../interfaces/currencies";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

interface ConvertReviewProps {
  quote: Quote;
}

function ConvertReview({ quote, componentId }: ConvertReviewProps & NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  async function handleSubmit() {
    try {
      setSubmitStatus("sending");
      const token = await SessionStorage.getAccessToken();
      await new BackendClient(token).executeQuote(quote.quoteId);
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
                  const [
                    fromDiemCurrencyCode,
                    toDiemCurrencyCode,
                  ] = quote.rfq.currency_pair.split("_");
                  const fromDiemCurrency = diemCurrencies[fromDiemCurrencyCode as DiemCurrency];
                  const toDiemCurrency = diemCurrencies[toDiemCurrencyCode as DiemCurrency];

                  const exchangeRate =
                    rates[fromDiemCurrencyCode as DiemCurrency][
                      toDiemCurrencyCode as DiemCurrency
                    ];

                  return (
                    <View style={theme.Container}>
                      {errorMessage && <ErrorMessage message={errorMessage} />}

                      <View style={theme.Section}>
                        <Text h1>{t("convert.review.title")}</Text>
                        <Text>{t("convert.review.description")}</Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("convert.review.amount")}</Text>
                        <Text style={{ color: "black" }}>
                          {diemToHumanFriendly(quote.rfq.amount, true)} {fromDiemCurrency.sign}
                        </Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("convert.review.price")}</Text>
                        <Text style={{ color: "black" }}>
                          {diemToHumanFriendly(quote.price, true)} {toDiemCurrency.sign}
                        </Text>
                      </View>

                      <View style={theme.Section}>
                        <Text>{t("convert.review.exchange_rate")}</Text>
                        <Text style={{ color: "black" }}>
                          1 {fromDiemCurrency.sign} = {diemToHumanFriendly(exchangeRate)}{" "}
                          {toDiemCurrency.sign}
                        </Text>
                      </View>

                      {submitStatus !== "success" && (
                        <>
                          <Button
                            containerStyle={theme.Section}
                            title={t("convert.review.confirm")}
                            disabled={submitStatus === "sending"}
                            onPress={handleSubmit}
                          />
                          <Button
                            type="outline"
                            title={t("convert.review.back")}
                            disabled={submitStatus === "sending"}
                            onPress={goBack}
                          />
                        </>
                      )}
                      {submitStatus === "success" && (
                        <>
                          <Button title={t("convert.review.done")} onPress={goToRoot} />
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

export default withRatesContext(withAccountContext(withUserContext(ConvertReview)));
