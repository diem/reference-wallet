// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { countries } from "countries-list";
import moment from "moment";
import { UserInfo } from "../../interfaces/user";
import { appTheme } from "../../styles";
import { IdentityInfo } from "./interfaces";
import SelectDropdown from "../../components/Select";
import { Keyboard, View } from "react-native";
import InputErrorMessage from "../../components/InputErrorMessage";
import DatePicker from "../../components/DatePicker";

const phonePrefixes = Object.keys(countries).reduce((list, code) => {
  const country = countries[code as keyof typeof countries];
  const phone = country.phone.split(",")[0];
  list[phone] = `+${phone} ${country.emoji}`;
  return list;
}, {} as Record<string, string>);

interface Step1IdentityProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
}

function Step1Identity({ info, onSubmit }: Step1IdentityProps) {
  const { t } = useTranslation("verify");
  const { errors, handleSubmit, control, setValue } = useForm<IdentityInfo>();

  const [phonePrefix, phoneNumber] = info.phone.split(" ");

  useEffect(() => {
    setValue("first_name", info.first_name);
    setValue("last_name", info.last_name);
    setValue("dob", info.dob);
    setValue("phone_prefix", phonePrefix);
    setValue("phone_number", phoneNumber);
  }, [info]);

  function onFormSubmit({ first_name, last_name, dob, phone_number, phone_prefix }: IdentityInfo) {
    Keyboard.dismiss();
    onSubmit({ ...info, first_name, last_name, dob, phone: `${phone_prefix} ${phone_number}` });
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step1.title")}</Text>
          <Text style={theme.Section}>{t("step1.description")}</Text>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="first_name"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step1.fields.first_name") },
                }),
              }}
              defaultValue={info.first_name}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step1.fields.first_name")} renderErrorMessage={false} />}
            />
            {!!errors.first_name && (
              <InputErrorMessage message={errors.first_name.message as string} />
            )}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="last_name"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step1.fields.last_name") },
                }),
              }}
              defaultValue={info.last_name}
              onChangeName="onChangeText"
              as={<Input placeholder={t("step1.fields.last_name")} renderErrorMessage={false} />}
            />
            {!!errors.last_name && (
              <InputErrorMessage message={errors.last_name.message as string} />
            )}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="dob"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step1.fields.dob") },
                }),
                validate: (selectedDate) => {
                  const date = moment.isMoment(selectedDate) ? selectedDate : moment(selectedDate);
                  if (!date.isValid()) {
                    return t("validations:validDate")!;
                  }
                  if (date.isAfter()) {
                    return t("validations:pastDateOnly")!;
                  }
                  return true;
                },
              }}
              defaultValue={info.dob}
              as={<DatePicker placeholder={t("step1.fields.dob")} />}
            />
            {!!errors.dob && <InputErrorMessage message={errors.dob.message as string} />}
          </View>

          <View style={theme.Section}>
            <Controller
              disabled={true}
              control={control}
              name="phone_number"
              rules={{
                required: t<string>("validations:required", {
                  replace: { field: t("step1.fields.phone_number") },
                }),
                pattern: {
                  value: new RegExp("^[0-9-s()]*$"),
                  message: t<string>("validations:numbersOnly", {
                    replace: { field: t("step1.fields.phone_number") },
                  }),
                },
              }}
              defaultValue={phoneNumber}
              onChangeName="onChangeText"
              as={<Input keyboardType="phone-pad" placeholder={t("step1.fields.phone_number")} />}
              leftIcon={
                <Controller
                  disabled={true}
                  control={control}
                  name="phone_prefix"
                  rules={{
                    required: t<string>("validations:required", {
                      replace: { field: t("step1.fields.phone_prefix") },
                    }),
                  }}
                  defaultValue={phonePrefix}
                  onChangeName="onChange"
                  as={
                    <SelectDropdown
                      label={t("step1.fields.phone_prefix")}
                      options={phonePrefixes}
                      disableStyles={true}
                    />
                  }
                />
              }
            />
            {!!errors.phone_prefix && (
              <InputErrorMessage message={errors.phone_prefix.message as string} />
            )}
            {!!errors.phone_number && (
              <InputErrorMessage message={errors.phone_number.message as string} />
            )}
          </View>

          <Button title={t("step1.continue")} onPress={handleSubmit(onFormSubmit)} />
        </>
      )}
    </ThemeConsumer>
  );
}

export default Step1Identity;
