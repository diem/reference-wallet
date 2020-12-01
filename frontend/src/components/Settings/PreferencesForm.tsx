// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useContext, useState } from "react";
import { Button, Form, FormGroup, FormText, Input } from "reactstrap";
import { useTranslation } from "react-i18next";
import SelectDropdown from "../select";
import { FiatCurrency } from "../../interfaces/currencies";
import i18next, { Languages } from "../../i18n";
import { settingsContext } from "../../contexts/app";

interface PreferencesFormProps {
  onSubmit: (value: { language: string; defaultFiatCurrencyCode: FiatCurrency }) => void;
}

function PreferencesForm({ onSubmit }: PreferencesFormProps) {
  const { t } = useTranslation("settings");

  const [settings] = useContext(settingsContext)!;

  const [defaultFiatCurrencyCode, setDefaultFiatCurrencyCode] = useState<FiatCurrency | undefined>(
    settings.defaultFiatCurrencyCode
  );
  const [language, setLanguage] = useState<string>(i18next.language);

  if (!settings.user) {
    return null;
  }

  async function onFormSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({ language, defaultFiatCurrencyCode: defaultFiatCurrencyCode! });
  }

  const fiatCurrencies: { [key in FiatCurrency]?: string } = Object.keys(
    settings.fiatCurrencies
  ).reduce((currencies, fiat) => {
    const currency = settings.fiatCurrencies[fiat];
    currencies[fiat] = `${currency.sign} ${currency.symbol}`;
    return currencies;
  }, {});

  const languages: { [key in string]: string } = Languages.reduce((languages, lang) => {
    languages[lang] = lang.toUpperCase();
    return languages;
  }, {});

  return (
    <Form onSubmit={onFormSubmit}>
      <h2 className="h5 font-weight-normal text-body">{t("preferences.general.title")}</h2>

      <FormGroup className="mb-4">
        <FormText>
          {process.env.NODE_ENV === "production"
            ? t("preferences.general.username")
            : t("preferences.general.email")}
        </FormText>
        <Input
          placeholder={
            process.env.NODE_ENV === "production"
              ? t("preferences.general.username")
              : t("preferences.general.email")
          }
          disabled
          value={settings.user.username}
        />
      </FormGroup>

      <h2 className="h5 font-weight-normal text-body">{t("preferences.form.title")}</h2>

      <FormGroup>
        <FormText>{t("preferences.form.fiat_currency")}</FormText>
        <SelectDropdown
          options={fiatCurrencies}
          value={defaultFiatCurrencyCode}
          onChange={(val) => setDefaultFiatCurrencyCode(val)}
        />
      </FormGroup>

      <FormGroup className="mb-4">
        <FormText>{t("preferences.form.language")}</FormText>
        <SelectDropdown options={languages} value={language} onChange={(val) => setLanguage(val)} />
      </FormGroup>

      <Button type="submit" color="black" block>
        {t("preferences.form.submit")}
      </Button>
    </Form>
  );
}

export default PreferencesForm;
