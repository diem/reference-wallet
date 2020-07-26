// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { SafeAreaView, ScrollView } from "react-native";
import { NavigationComponentProps } from "react-native-navigation";
import { ThemeProvider } from "react-native-elements";
import AppHeader from "./AppHeader";
import { appTheme } from "../styles";

interface ScreenLayoutProps {
  hideHeaderBack?: boolean;
}

function ScreenLayout({
  hideHeaderBack,
  componentId,
  children,
}: React.PropsWithChildren<ScreenLayoutProps & NavigationComponentProps>) {
  return (
    <ThemeProvider theme={appTheme}>
      <SafeAreaView style={appTheme.Screen}>
        <AppHeader componentId={componentId} showBackButton={!hideHeaderBack} />
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
