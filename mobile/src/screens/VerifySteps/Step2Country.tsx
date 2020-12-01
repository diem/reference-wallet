// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { countries } from "countries-list";
import { UserInfo } from "../../interfaces/user";
import { appTheme } from "../../styles";
import { CountryInfo } from "./interfaces";
import { Keyboard, View } from "react-native";
import SelectDropdown from "../../components/Select";
import InputErrorMessage from "../../components/InputErrorMessage";

type CountriesList = {
  [key in keyof typeof countries]: string;
};

export const countriesList = Object.keys(countries)
  .sort((a, b) => {
    const countryA = countries[a as keyof typeof countries];
    const countryB = countries[b as keyof typeof countries];
    return countryA.name.localeCompare(countryB.name);
  })
  .reduce((list, code) => {
    const country = countries[code as keyof typeof countries];
    list[code as keyof typeof countries] = `${country.emoji} ${country.name} (${country.native})`;
    return list;
  }, {} as CountriesList);

interface Step2CountryProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
  onBack: () => void;
}

function Step2Country({ info, onSubmit, onBack }: Step2CountryProps) {
  const { t } = useTranslation("verify");
  const { errors, handleSubmit, control, setValue } = useForm<CountryInfo>();

  useEffect(() => {
    setValue("country", info.country!);
  }, [info]);

  function onFormSubmit({ country }: CountryInfo) {
    Keyboard.dismiss();
    onSubmit({ ...info, country });
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step2.title")}</Text>
          <Text style={theme.Section}>{t("step2.description")}</Text>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="country"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step2.fields.country") },
                }),
              }}
              defaultValue={info.country}
              onChangeName="onChange"
              as={<SelectDropdown label={t("step2.fields.country")} options={countriesList} />}
            />
            {!!errors.country && <InputErrorMessage message={errors.country.message as string} />}
          </View>

          <View style={theme.ButtonsGroup.containerStyle}>
            <Button
              type="outline"
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step2.back")}
              onPress={onBack}
            />
            <Button
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

export default Step2Country;
