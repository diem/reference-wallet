// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Keyboard, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { BackendError } from "../services/errors";
import BackendClient from "../services/backendClient";
import ErrorMessage from "../components/Messages/ErrorMessage";
import InputErrorMessage from "../components/InputErrorMessage";

interface ResetPasswordForm {
  new_password: string;
  confirm_password: string;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

interface ResetPasswordProps {
  token: string;
}

function ResetPassword({ token, componentId }: ResetPasswordProps & NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control } = useForm<ResetPasswordForm>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  const passwordStrengthRegex = new RegExp("^(?=.*\\d)(?=.*[a-zA-Z]).{8,}$");

  async function onFormSubmit({ new_password, confirm_password }: ResetPasswordForm) {
    if (!passwordStrengthRegex.test(new_password)) {
      return setErrorMessage(t("fields.password_strength.error"));
    }
    if (new_password !== confirm_password) {
      return setErrorMessage(t("reset_password.password_mismatch"));
    }

    try {
      Keyboard.dismiss();
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      await new BackendClient().resetUserPassword(token, new_password);
      setSubmitStatus("success");

      await Navigation.popToRoot(componentId);
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

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            <Text h1>{t("reset_password.headline")}</Text>

            {errorMessage && <ErrorMessage message={errorMessage} />}

            <Text style={theme.Section}>{t("reset_password.text")}</Text>
            <View style={theme.Section}>
              <Controller
                control={control}
                name="new_password"
                rules={{
                  required: t<string>("validations:required", {
                    replace: { field: t("fields.new_password") },
                  }),
                }}
                onChangeName="onChangeText"
                as={
                  <Input
                    secureTextEntry={true}
                    placeholder={t("fields.new_password")}
                    renderErrorMessage={false}
                  />
                }
              />
              {!!errors.new_password && (
                <InputErrorMessage message={errors.new_password.message as string} />
              )}
            </View>

            <View style={theme.Section}>
              <Controller
                control={control}
                name="confirm_password"
                rules={{
                  required: t<string>("validations:required", {
                    replace: { field: t("fields.confirm_password") },
                  }),
                }}
                onChangeName="onChangeText"
                as={
                  <Input
                    secureTextEntry={true}
                    placeholder={t("fields.confirm_password")}
                    renderErrorMessage={false}
                  />
                }
              />
              {!!errors.confirm_password && (
                <InputErrorMessage message={errors.confirm_password.message as string} />
              )}
            </View>
            <Button
              title={t("reset_password.submit")}
              onPress={handleSubmit(onFormSubmit)}
              loading={submitStatus === "sending"}
            />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default ResetPassword;
