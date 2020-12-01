// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { appTheme } from "../styles";

function TestnetWarning() {
  const { t } = useTranslation("legal");

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={StyleSheet.flatten([theme.ExampleSection, theme.Section])}>
          <Text style={theme.ExampleSectionText}>{t("testnet_warning")}</Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default TestnetWarning;
