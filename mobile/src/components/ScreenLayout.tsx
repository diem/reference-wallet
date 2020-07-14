// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { SafeAreaView, ScrollView } from "react-native";
import { NavigationComponentProps } from "react-native-navigation";
import { ThemeProvider } from "react-native-elements";
import AppHeader from "./AppHeader";
import { appTheme } from "../styles";

function ScreenLayout({
  componentId,
  children,
}: React.PropsWithChildren<NavigationComponentProps>) {
  return (
    <ThemeProvider theme={appTheme}>
      <SafeAreaView style={appTheme.Screen}>
        <AppHeader componentId={componentId} />
        <ScrollView
          style={appTheme.ScrollArea}
          contentContainerStyle={appTheme.ScrollAreaContent}
          contentInsetAdjustmentBehavior="automatic"
        >
          {children}
        </ScrollView>
      </SafeAreaView>
    </ThemeProvider>
  );
}

export default ScreenLayout;
