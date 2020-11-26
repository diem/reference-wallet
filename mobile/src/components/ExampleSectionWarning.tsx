// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { View } from "react-native";
import { Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { appTheme } from "../styles";

function ExampleSectionWarning() {
  const { t } = useTranslation("legal");

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={theme.ExampleSection}>
          <Text style={theme.ExampleSectionText}>{t("example_section_warning")}</Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default ExampleSectionWarning;
