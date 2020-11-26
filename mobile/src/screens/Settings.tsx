// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { userContext, withUserContext } from "../contexts/user";
import SessionStorage from "../services/sessionStorage";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import BackendClient from "../services/backendClient";
import i18next from "i18next";
import { BackendError } from "../services/errors";
import { useTranslation } from "react-i18next";
import PreferencesForm from "../components/PreferencesForm";
import ErrorMessage from "../components/Messages/ErrorMessage";
import { FiatCurrency } from "../interfaces/currencies";
import PaymentMethodsForm from "../components/PaymentMethodsForm";
import { NewPaymentMethod, RegistrationStatus } from "../interfaces/user";

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function Settings({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("settings");

  const user = useContext(userContext);

  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");
  const [errorMessage, setErrorMessage] = useState<string>();

  const userVerificationRequired =
    user && user.registration_status === RegistrationStatus.Registered;

  async function storePaymentMethod(paymentMethod: NewPaymentMethod) {
    try {
      setSubmitStatus("sending");
      const token = await SessionStorage.getAccessToken();
      await new BackendClient(token).storePaymentMethod(
        paymentMethod.name,
        paymentMethod.provider,
        paymentMethod.token
      );
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

  async function savePreferences({
    selectedFiatCurrency,
    selectedLanguage,
  }: {
    selectedFiatCurrency: FiatCurrency;
    selectedLanguage: string;
  }) {
    try {
      setSubmitStatus("sending");
      const token = await SessionStorage.getAccessToken();
      await new BackendClient(token).updateUserSettings(selectedLanguage, selectedFiatCurrency);

      if (selectedLanguage !== user?.selected_language) {
        await i18next.changeLanguage(selectedLanguage);
      }

      await Navigation.popToRoot(componentId);
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

  async function logout() {
    await SessionStorage.removeAccessToken();
    await Navigation.setStackRoot(componentId, {
      component: {
        name: "SignIn",
      },
    });
  }
  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {user ? (
              <View style={theme.Container}>
                {errorMessage && <ErrorMessage message={errorMessage} />}

                <View style={theme.Section}>
                  <Text style={theme.Title}>{t("title")}</Text>
                </View>

                {!userVerificationRequired && (
                  <PaymentMethodsForm
                    user={user}
                    componentId={componentId}
                    paymentMethods={user.paymentMethods!}
                    onAdd={storePaymentMethod}
                  />
                )}

                <PreferencesForm
                  email={user.username}
                  fiatCurrency={user.selected_fiat_currency}
                  language={user.selected_language}
                  onSubmit={savePreferences}
                />

                <Button type="outline" title={t("logout")} onPress={logout} />
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

export default withUserContext(Settings);
