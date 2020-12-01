// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { StyleSheet, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";

function Transfer({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            <Text style={StyleSheet.flatten([theme.Title, theme.Section])}>{t("title")}</Text>
            <View style={theme.Section}>
              <Button
                type="outline"
                title={t("modes.deposit")}
                onPress={() => {
                  Navigation.push(componentId, {
                    component: {
                      name: "Deposit",
                    },
                  });
                }}
              />
            </View>
            <View style={theme.Section}>
              <Button
                type="outline"
                title={t("modes.withdraw")}
                onPress={() => {
                  Navigation.push(componentId, {
                    component: {
                      name: "Withdraw",
                    },
                  });
                }}
              />
            </View>
            <View style={theme.Section}>
              <Button
                type="outline"
                title={t("modes.convert")}
                onPress={() => {
                  Navigation.push(componentId, {
                    component: {
                      name: "Convert",
                    },
                  });
                }}
              />
            </View>
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default Transfer;
