// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { View } from "react-native";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import SelectDropdown from "./Select";
import { fiatCurrenciesOptions, languagesOptions } from "../utils/dropdown-options";
import React from "react";
import { useState } from "react";
import { appTheme } from "../styles";
import { FiatCurrency } from "../interfaces/currencies";
import { useTranslation } from "react-i18next";

interface PreferencesFormProps {
  email: string;
  language: string;
  fiatCurrency: FiatCurrency;
  onSubmit: (val: { selectedFiatCurrency: FiatCurrency; selectedLanguage: string }) => void;
}

function PreferencesForm({ email, language, fiatCurrency, onSubmit }: PreferencesFormProps) {
  const { t } = useTranslation("settings");

  const [selectedFiatCurrency, setSelectedFiatCurrency] = useState<FiatCurrency>(fiatCurrency);
  const [selectedLanguage, setSelectedLanguage] = useState<string>(language);

  function onFormSubmit() {
    onSubmit({ selectedFiatCurrency, selectedLanguage });
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <View style={theme.Section}>
            <Text style={theme.SubTitle}>{t("preferences.general.title")}</Text>
          </View>
          <View style={theme.Section}>
            <Text>{t("preferences.general.email")}</Text>
            <Input value={email} disabled={true} />
          </View>
          <View style={theme.Section}>
            <Text style={theme.SubTitle}>{t("preferences.form.title")}</Text>
          </View>
          <View style={theme.Section}>
            <Text>{t("preferences.form.fiat_currency")}</Text>
            <SelectDropdown
              value={selectedFiatCurrency}
              options={fiatCurrenciesOptions()}
              onChange={(val) => setSelectedFiatCurrency(val)}
            />
          </View>
          <View style={theme.Section}>
            <Text>{t("preferences.form.language")}</Text>
            <SelectDropdown
              value={selectedLanguage}
              options={languagesOptions()}
              onChange={(val) => setSelectedLanguage(val as string)}
            />
          </View>
          <Button title={t("preferences.form.submit")} onPress={onFormSubmit} />
        </>
      )}
    </ThemeConsumer>
  );
}

export default PreferencesForm;
