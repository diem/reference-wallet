// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { Trans, useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import ErrorMessage from "../components/Messages/ErrorMessage";
import InfoMessage from "../components/Messages/InfoMessage";
import InputErrorMessage from "../components/InputErrorMessage";

interface ForgotPasswordForm {
  email: string;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function ForgotPassword({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control, watch } = useForm<ForgotPasswordForm>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  async function onFormSubmit({ email }: ForgotPasswordForm) {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const token = await new BackendClient().forgotPassword(email);
      setSubmitStatus("success");

      setTimeout(() => {
        Navigation.push(componentId, {
          component: {
            name: "ResetPassword",
            passProps: { token },
          },
        });
      }, 3000);
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
            <Text h1>{t("forgot_password.headline")}</Text>

            {errorMessage && <ErrorMessage message={errorMessage} />}
            {submitStatus === "success" && (
              <InfoMessage
                message={t("forgot_password.success", { replace: { email: watch("email") } })}
              />
            )}

            <Text style={theme.Section}>
              <Trans
                t={t}
                i18nKey="forgot_password.text"
                components={[
                  <Text
                    style={theme.PrimaryLink}
                    onPress={() => {
                      Navigation.push(componentId, {
                        component: {
                          name: "SignUp",
                        },
                      });
                    }}
                  >
                    sign up
                  </Text>,
                  <Text
                    style={theme.PrimaryLink}
                    onPress={() => {
                      Navigation.popToRoot(componentId);
                    }}
                  >
                    log in
                  </Text>,
                ]}
              />
            </Text>
            <View style={theme.Section}>
              <Controller
                control={control}
                name="email"
                rules={{
                  required: t<string>("validations:required", {
                    replace: { field: t("fields.email") },
                  }),
                }}
                onChangeName="onChangeText"
                as={
                  <Input
                    autoCompleteType="email"
                    keyboardType="email-address"
                    placeholder={t("fields.email")}
                    renderErrorMessage={false}
                  />
                }
              />
              {!!errors.email && <InputErrorMessage message={errors.email.message as string} />}
            </View>
            <Button title={t("forgot_password.submit")} onPress={handleSubmit(onFormSubmit)} />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default ForgotPassword;
