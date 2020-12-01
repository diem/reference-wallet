// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { UserInfo } from "../../interfaces/user";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../../styles";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { Keyboard, View } from "react-native";
import { DefaultSettings } from "./interfaces";
import SelectDropdown from "../../components/Select";
import { fiatCurrenciesOptions } from "../../utils/dropdown-options";
import InputErrorMessage from "../../components/InputErrorMessage";

interface Step5DefaultCurrencyProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
  onBack: () => void;
}

function Step5DefaultCurrency({ info, onSubmit, onBack }: Step5DefaultCurrencyProps) {
  const { t } = useTranslation("verify");
  const { errors, handleSubmit, control } = useForm<DefaultSettings>();
  const [loading, setLoading] = useState<boolean>(false);

  function onFormSubmit({ default_fiat_currency }: DefaultSettings) {
    setLoading(true);
    Keyboard.dismiss();
    onSubmit({ ...info, selected_fiat_currency: default_fiat_currency });
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step5.title")}</Text>
          <Text style={theme.Section}>{t("step5.description")}</Text>

          <View style={theme.Section}>
            <Controller
              control={control}
              name="default_fiat_currency"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step5.fields.default_fiat_currency") },
                }),
              }}
              defaultValue={info.selected_fiat_currency}
              onChangeName="onChange"
              as={
                <SelectDropdown
                  label={t("step5.fields.default_fiat_currency")}
                  options={fiatCurrenciesOptions()}
                />
              }
            />
            {!!errors.default_fiat_currency && (
              <InputErrorMessage message={errors.default_fiat_currency.message as string} />
            )}
          </View>

          <View style={theme.ButtonsGroup.containerStyle}>
            <Button
              type="outline"
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step2.back")}
              onPress={onBack}
            />
            <Button
              loading={loading}
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step2.continue")}
              onPress={handleSubmit(onFormSubmit)}
            />
          </View>
        </>
      )}
    </ThemeConsumer>
  );
}

export default Step5DefaultCurrency;
