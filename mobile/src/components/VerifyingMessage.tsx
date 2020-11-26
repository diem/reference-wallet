// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { appTheme } from "../styles";
import {View} from "react-native";

function VerifyingMessage() {
  const { t } = useTranslation("layout");

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={theme.Container}>
          <Text h1>{t("verification_pending.title")}</Text>
          <Text style={theme.Section}>{t("verification_pending.description")}</Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default VerifyingMessage;
