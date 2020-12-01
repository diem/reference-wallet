// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Keyboard, View } from "react-native";
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
import { isProd } from "../../index";

interface SignInForm {
  username: string;
  password: string;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function SignIn({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control } = useForm<SignInForm>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  async function onFormSubmit({ username, password }: SignInForm) {
    try {
      Keyboard.dismiss();
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const authToken = await new BackendClient().signinUser(username, password);
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
    <ScreenLayout hideHeaderBack={true} showLegalDisclaimer={true} componentId={componentId}>
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
                name="username"
                rules={{
                  required: t<string>("validations:required", {
                    replace: { field: isProd ? t("fields.username") : t("fields.email") },
                  }),
                }}
                onChangeName="onChangeText"
                as={
                  isProd ? (
                    <Input placeholder={t("fields.username")} renderErrorMessage={false} />
                  ) : (
                    <Input
                      autoCompleteType="email"
                      keyboardType="email-address"
                      placeholder={t("fields.email")}
                      renderErrorMessage={false}
                    />
                  )
                }
              />
              {!!errors.username && (
                <InputErrorMessage message={errors.username.message as string} />
              )}
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
            <Button
              title={t("signin.submit")}
              onPress={handleSubmit(onFormSubmit)}
              loading={submitStatus === "sending"}
            />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default SignIn;
