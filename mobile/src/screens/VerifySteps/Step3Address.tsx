// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { UserInfo } from "../../interfaces/user";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../../styles";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { AddressInfo } from "./interfaces";
import { useEffect } from "react";
import { Keyboard, View } from "react-native";
import InputErrorMessage from "../../components/InputErrorMessage";

interface Step3AddressProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
  onBack: () => void;
}

function Step3Address({ info, onSubmit, onBack }: Step3AddressProps) {
  const { t } = useTranslation("verify");
  const { errors, handleSubmit, control, setValue } = useForm<AddressInfo>();

  useEffect(() => {
    setValue("address_1", info.address_1);
    setValue("address_2", info.address_2);
    setValue("city", info.city);
    setValue("state", info.state);
    setValue("zip", info.zip);
  }, [info]);

  function onFormSubmit({ address_1, address_2, city, state, zip }: AddressInfo) {
    Keyboard.dismiss();
    onSubmit({ ...info, address_1, address_2, city, state, zip });
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step3.title")}</Text>
          <Text style={theme.Section}>{t("step3.description")}</Text>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="address_1"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step3.fields.address_1") },
                }),
              }}
              defaultValue={info.address_1}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step3.fields.address_1")} renderErrorMessage={false} />}
            />
            {!!errors.address_1 && (
              <InputErrorMessage message={errors.address_1.message as string} />
            )}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="address_2"
              defaultValue={info.address_2}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step3.fields.address_2")} renderErrorMessage={false} />}
            />
            {!!errors.address_2 && (
              <InputErrorMessage message={errors.address_2.message as string} />
            )}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="city"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step3.fields.city") },
                }),
              }}
              defaultValue={info.city}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step3.fields.city")} renderErrorMessage={false} />}
            />
            {!!errors.city && <InputErrorMessage message={errors.city.message as string} />}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="state"
              defaultValue={info.state}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step3.fields.state")} renderErrorMessage={false} />}
            />
            {!!errors.state && <InputErrorMessage message={errors.state.message as string} />}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="zip"
              defaultValue={info.zip}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step3.fields.zip")} renderErrorMessage={false} />}
            />
            {!!errors.zip && <InputErrorMessage message={errors.zip.message as string} />}
          </View>

          <View style={theme.ButtonsGroup.containerStyle}>
            <Button
              type="outline"
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step3.back")}
              onPress={onBack}
            />
            <Button
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step3.continue")}
              onPress={handleSubmit(onFormSubmit)}
            />
          </View>
        </>
      )}
    </ThemeConsumer>
  );
}

export default Step3Address;
