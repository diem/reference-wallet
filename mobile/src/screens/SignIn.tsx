// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useState } from "react";
import { View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { Controller, useForm } from "react-hook-form";
import { Trans, useTranslation } from "react-i18next";
import { appTheme } from "../styles";
import BackendClient from "../services/backendClient";
import SessionStorage from "../services/sessionStorage";
import { BackendError } from "../services/errors";
import ScreenLayout from "../components/ScreenLayout";
import ErrorMessage from "../components/Messages/ErrorMessage";
import InputErrorMessage from "../components/InputErrorMessage";

interface SignInForm {
  email: string;
  password: string;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function SignIn({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control } = useForm<SignInForm>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  async function onFormSubmit({ email, password }: SignInForm) {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const authToken = await new BackendClient().signinUser(email, password);
      await SessionStorage.storeAccessToken(authToken);
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

  async function redirectLoggedIn() {
    if (await SessionStorage.getAccessToken()) {
      await Navigation.setStackRoot(componentId, {
        component: {
          name: "Home",
        },
      });
    }
  }
  redirectLoggedIn();

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            {errorMessage && <ErrorMessage message={errorMessage} />}

            <Text h1>{t("signin.headline")}</Text>
            <Text style={theme.Section}>
              <Trans t={t} i18nKey="signin.text" values={{ name: t("layout:name") }}>
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
                  Sign up
                </Text>
              </Trans>
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

            <View style={theme.Section}>
              <Controller
                control={control}
                name="password"
                rules={{
                  required: t<string>("validations:required", {
                    replace: { field: t("fields.password") },
                  }),
                }}
                onChangeName="onChangeText"
                as={
                  <Input
                    secureTextEntry={true}
                    placeholder={t("fields.password")}
                    renderErrorMessage={false}
                  />
                }
              />
              {!!errors.password && (
                <InputErrorMessage message={errors.password.message as string} />
              )}

              <Text
                style={theme.SmallLink}
                onPress={() => {
                  Navigation.push(componentId, {
                    component: {
                      name: "ForgotPassword",
                    },
                  });
                }}
              >
                {t("signin.links.forgot_password")}
              </Text>
            </View>
            <Button title={t("signin.submit")} onPress={handleSubmit(onFormSubmit)} />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default SignIn;
