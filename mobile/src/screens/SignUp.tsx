// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { Keyboard, Linking, View } from "react-native";
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
import { isProd } from "../../index";

interface SignUpForm {
  username: string;
  password: string;
  agreed_tou: boolean;
}

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function SignUp({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("auth");

  const { errors, handleSubmit, control, watch, setValue } = useForm<SignUpForm>({
    defaultValues: { username: "", password: "", agreed_tou: false },
  });
  const { username, password, agreed_tou } = watch();

  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  const passwordStrengthRegex = new RegExp("^(?=.*\\d)(?=.*[a-zA-Z]).{8,}$");

  const onFormSubmit = async ({ username, password }: SignUpForm) => {
    if (!passwordStrengthRegex.test(password)) {
      return setErrorMessage(t("fields.password_strength.error"));
    }

    try {
      Keyboard.dismiss();
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const authToken = await new BackendClient().signupUser(username, password);
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

  useEffect(() => {
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
  }, [submitStatus]);

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            {errorMessage && <ErrorMessage message={errorMessage} />}

            {submitStatus === "success" &&
              (isProd ? (
                <>
                  <Text>{t("signup.success_username.headline")}</Text>
                  <Text>{t("signup.success_username.text", { replace: { email: username } })}</Text>
                </>
              ) : (
                <>
                  <Text>{t("signup.success_email.headline")}</Text>
                  <Text>{t("signup.success_email.text", { replace: { username } })}</Text>
                </>
              ))}

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
            </View>

            {!!password.length && (
              <View style={theme.Section}>
                <Text style={{ fontWeight: "bold" }}>
                  {t("fields.password_strength.title")}:{" "}
                  {passwordStrengthRegex.test(password) ? (
                    <Text style={{ color: theme.colors!.success }}>
                      {t("fields.password_strength.strong")}
                    </Text>
                  ) : (
                    <Text style={{ color: theme.colors!.warning }}>
                      {t("fields.password_strength.weak")}
                    </Text>
                  )}
                </Text>
                <Text>{t("fields.password_strength.text")}</Text>
              </View>
            )}

            <View style={theme.Section}>
              <Controller
                control={control}
                name="agreed_tou"
                rules={{
                  required: t<string>("validations:required", {
                    replace: {
                      field: t("fields.agree_terms", {
                        replace: [],
                      }),
                    },
                  }),
                }}
                valueName="checked"
                onChangeName="onPress"
                as={(props) => {
                  return (
                    <CheckBox
                      {...props}
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
                      onPress={() => {
                        setValue("agreed_tou", !agreed_tou);
                      }}
                    />
                  );
                }}
              />
              {!!errors.agreed_tou && (
                <InputErrorMessage message={errors.agreed_tou.message as string} />
              )}
            </View>
            <Button
              title={t("signup.submit")}
              onPress={handleSubmit(onFormSubmit)}
              loading={submitStatus === "sending"}
            />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default SignUp;
