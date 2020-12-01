// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text } from "react-native-elements";
import { View } from "react-native";
import { useTranslation } from "react-i18next";

function LegalDisclaimer() {
  const { t } = useTranslation("legal");

  return (
    <View
      style={{
        height: "100%",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
    >
      <Text style={{ textAlign: "justify" }}>{t("legal_disclaimer")}</Text>
    </View>
  );
}

export default LegalDisclaimer;
