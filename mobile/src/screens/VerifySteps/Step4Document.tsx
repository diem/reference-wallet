// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { UserInfo } from "../../interfaces/user";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../../styles";
import { Trans, useTranslation } from "react-i18next";
import { Keyboard, View } from "react-native";
import { countries } from "countries-list";

interface Step4DocumentProps {
  info: UserInfo;
  onSubmit: (value: any) => void;
  onBack: () => void;
}

function Step4Document({ info, onSubmit, onBack }: Step4DocumentProps) {
  const { t } = useTranslation("verify");

  const onFormSubmit = async () => {
    Keyboard.dismiss();
    onSubmit(undefined);
  };

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step4.title")}</Text>
          <Text style={theme.Section}>{t("step4.description")}</Text>

          <View
            style={{
              borderWidth: 1,
              borderColor: "#dfdfdf",
              borderRadius: 8,
              marginBottom: 24,
            }}
          >
            <View
              style={{
                padding: 16,
              }}
            >
              <Text style={{ color: "#000000" }}>
                <Trans t={t} i18nKey="step4.input.description">
                  <Text style={{ color: "#000000", fontWeight: "bold" }}>
                    {{ country: countries[info.country as keyof typeof countries].name }}
                  </Text>
                </Trans>
              </Text>
              <View style={{ padding: 16 }}>
                <Text style={{ color: "#000" }}>{t("step4.input.passport")}</Text>
                <Text style={{ color: "#000" }}>{t("step4.input.drivers_license")}</Text>
                <Text style={{ color: "#000" }}>{t("step4.input.identity_card")}</Text>
              </View>
            </View>

            <View
              style={{
                backgroundColor: "#f7f7f7",
                borderTopColor: "#dfdfdf",
                borderTopWidth: 1,
                padding: 16,
              }}
            >
              <Text style={{ color: "#000000" }}>{t("step4.input.upload")}</Text>
            </View>
          </View>

          <View style={theme.ButtonsGroup.containerStyle}>
            <Button
              type="outline"
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step4.back")}
              onPress={onBack}
            />
            <Button
              containerStyle={theme.ButtonsGroup.buttonStyle}
              title={t("step4.continue")}
              onPress={onFormSubmit}
            />
          </View>
        </>
      )}
    </ThemeConsumer>
  );
}

export default Step4Document;
