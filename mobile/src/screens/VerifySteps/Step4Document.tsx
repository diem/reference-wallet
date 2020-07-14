// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { UserInfo } from "../../interfaces/user";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../../styles";
import { useTranslation } from "react-i18next";
import { View } from "react-native";

interface Step4DocumentProps {
  info: UserInfo;
  onSubmit: (value: any) => void;
  onBack: () => void;
}

function Step4Document({ info, onSubmit, onBack }: Step4DocumentProps) {
  const { t } = useTranslation("verify");

  const onFormSubmit = async () => {
    onSubmit(undefined);
  };

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <Text h1>{t("step4.title")}</Text>
          <Text style={theme.Section}>{t("step4.description")}</Text>

          <View style={theme.ButtonsGroup}>
            <Button
              containerStyle={theme.ButtonsGroupButton}
              title={t("step4.back")}
              onPress={onBack}
            />
            <Button
              containerStyle={theme.ButtonsGroupButton}
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
