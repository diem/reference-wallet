// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, Container } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import SessionStorage from "../services/sessionStorage";
import BackendClient from "../services/backendClient";
import PaymentMethodsForm from "../components/Settings/PaymentMethodsForm";
import PreferencesForm from "../components/Settings/PreferencesForm";
import Breadcrumbs from "../components/Breadcrumbs";
import i18next from "../i18n";
import { BackendError } from "../services/errors";
import { FiatCurrency } from "../interfaces/currencies";
import ErrorMessage from "../components/Messages/ErrorMessage";
import SuccessMessage from "components/Messages/SuccessMessage";
import { NewPaymentMethod, PaymentMethod, RegistrationStatus } from "../interfaces/user";
import { Redirect } from "react-router";

type FormStages = "edit" | "sending" | "fail" | "success" | "redirect";

const Settings = () => {
  const { t } = useTranslation("settings");
  const [settings, setSettings] = useContext(settingsContext)!;

  const [formStage, setFormStage] = useState<FormStages>("edit");
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>(
    settings.paymentMethods || []
  );

  const userVerificationRequired =
    settings.user && settings.user.registration_status === RegistrationStatus.Registered;

  useEffect(() => {
    async function refreshUser() {
      try {
        await new BackendClient().refreshUser();
      } catch (e) {
        console.error(e);
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();
  }, []);

  async function fetchPaymentMethods() {
    try {
      const backendClient = new BackendClient();
      setPaymentMethods(await backendClient.getPaymentMethods());
    } catch (e) {
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  }

  useEffect(() => {
    // noinspection JSIgnoredPromiseFromCall
    fetchPaymentMethods();
  }, []);

  async function savePreferences({
    language,
    defaultFiatCurrencyCode,
  }: {
    language: string;
    defaultFiatCurrencyCode: FiatCurrency;
  }) {
    try {
      setFormStage("sending");
      const backendClient = new BackendClient();
      await backendClient.updateUserSettings(language, defaultFiatCurrencyCode);

      if (language !== settings.language) {
        await i18next.changeLanguage(language);
      }

      setSettings({ ...settings, defaultFiatCurrencyCode, language });
      await fetchPaymentMethods();
      setFormStage("redirect");
    } catch (e) {
      setFormStage("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  }

  async function storePaymentMethod(paymentMethod: NewPaymentMethod) {
    try {
      setFormStage("sending");
      const backendClient = new BackendClient();
      await backendClient.storePaymentMethod(
        paymentMethod.name,
        paymentMethod.provider,
        paymentMethod.token
      );
      await fetchPaymentMethods();
      setFormStage("success");
    } catch (e) {
      setFormStage("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  }

  async function logout() {
    try {
      await new BackendClient().signoutUser();
    } catch (e) {
      console.error(e);
    }
    SessionStorage.removeAccessToken();
    setSettings({ ...settings, user: undefined });
  }

  if (formStage === "success") {
    setTimeout(() => setFormStage("edit"), 3000);
  }

  return (
    <>
      {formStage === "redirect" && <Redirect to="/" />}
      <Breadcrumbs pageName={t("title")} />
      <Container className="py-5 d-flex flex-column">
        <section className="slim-section m-auto">
          {formStage === "success" && <SuccessMessage message={t("success_message")} />}
          {errorMessage && <ErrorMessage message={errorMessage} />}

          {!userVerificationRequired && (
            <PaymentMethodsForm paymentMethods={paymentMethods} onAdd={storePaymentMethod} />
          )}
          <PreferencesForm onSubmit={savePreferences} />
          <Button outline color="black" block className="mt-4" onClick={logout}>
            {t("signout")}
          </Button>
        </section>
      </Container>
    </>
  );
};

export default Settings;
