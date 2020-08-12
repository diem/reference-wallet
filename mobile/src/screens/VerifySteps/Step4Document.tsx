// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { UserInfo } from "../../interfaces/user";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../../styles";
import { useTranslation } from "react-i18next";
import { Keyboard, View } from "react-native";

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
                For <Text style={{ color: "#000000", fontWeight: "bold" }}>Paraguay</Text>, please
                take a photo of one of the following government-issued IDs.
              </Text>
              <View style={{ padding: 16 }}>
                <Text style={{ color: "#000" }}>Passport</Text>
                <Text style={{ color: "#000" }}>Driver's License</Text>
                <Text style={{ color: "#000" }}>Identity Card</Text>
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
              <Text style={{ color: "#000000" }}>Drag and Drop or click here to select a file</Text>
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
