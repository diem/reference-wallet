// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { SafeAreaView, ScrollView } from "react-native";
import { NavigationComponentProps } from "react-native-navigation";
import { ThemeProvider } from "react-native-elements";
import AppHeader from "./AppHeader";
import { appTheme } from "../styles";
import LegalDisclaimer from "./LegalDisclaimer";

interface ScreenLayoutProps {
  hideHeaderBack?: boolean;
  showLegalDisclaimer?: boolean;
}

function ScreenLayout({
  showLegalDisclaimer = false,
  hideHeaderBack,
  componentId,
  children,
}: React.PropsWithChildren<ScreenLayoutProps & NavigationComponentProps>) {
  const [legalDisclaimer, setLegalDisclaimer] = useState(showLegalDisclaimer);

  useEffect(() => {
    setTimeout(() => setLegalDisclaimer(false), 5000);
  }, []);

  return (
    <ThemeProvider theme={appTheme}>
      <SafeAreaView style={appTheme.Screen}>
        <AppHeader componentId={componentId} showBackButton={!hideHeaderBack} />
        {legalDisclaimer ? (
          <LegalDisclaimer />
        ) : (
          <ScrollView
            style={appTheme.ScrollArea}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={appTheme.ScrollAreaContent}
            contentInsetAdjustmentBehavior="automatic"
          >
            {children}
          </ScrollView>
        )}
      </SafeAreaView>
    </ThemeProvider>
  );
}

export default ScreenLayout;
