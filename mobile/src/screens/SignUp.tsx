// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useState } from "react";
import { Linking, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, CheckBox, Input, Text, ThemeConsumer } from "react-native-elements";
import { Trans, useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import BackendClient from "../services/backendClient";
import SessionStorage from "../services/sessionStorage";
import { BackendError } from "../services/errors";
import ScreenLayout from "../components/ScreenLayout";
import ErrorMessage from "../components/Messages/ErrorMessage";
import { appTheme } from "../styles";
import InputErrorMessage from "../components/InputErrorMessage";

interface SignUpForm {
  email: string;
  password: string;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function SignUp({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control } = useForm<SignUpForm>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");
  const [agreedTerms, setAgreedTerms] = useState(false);

  const passwordStrengthRegex = new RegExp("^(?=.*\\d)(?=.*[a-zA-Z]).{8,}$");

  const onFormSubmit = async ({ email, password }: SignUpForm) => {
    if (!passwordStrengthRegex.test(password)) {
      return setErrorMessage(t("fields.password_strength.error"));
    }

    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const authToken = await new BackendClient().signupUser(email, password);
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
  };

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

            <Text h1>{t("signup.headline")}</Text>
            <Text style={theme.Section}>
              <Trans
                t={t}
                i18nKey="signup.text"
                components={[
                  <Text
                    style={theme.PrimaryLink}
                    onPress={() => {
                      Navigation.popToRoot(componentId);
                    }}
                  >
                    Log in
                  </Text>,
                ]}
                values={{ name: t("layout:name") }}
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
            </View>

            <View style={theme.Section}>
              <CheckBox
                checked={agreedTerms}
                uncheckedIcon="square"
                checkedIcon="check-square"
                title={
                  <Text style={theme.CheckBoxText}>
                    <Trans t={t} i18nKey="fields.agree_terms">
                      <Text
                        style={theme.PrimaryLink}
                        onPress={() => {
                          Linking.openURL("http://google.com");
                        }}
                      >
                        Terms and Conditions
                      </Text>
                    </Trans>
                  </Text>
                }
                onPress={() => setAgreedTerms(!agreedTerms)}
              />
            </View>
            <Button title={t("signup.submit")} onPress={handleSubmit(onFormSubmit)} />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default SignUp;
