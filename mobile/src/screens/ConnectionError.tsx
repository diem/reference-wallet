// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import ScreenLayout from "../components/ScreenLayout";
import { Button, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";
import { View, Text } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";

function ConnectionError({ componentId }: NavigationComponentProps) {
  const tryAgain = async () => {
    await Navigation.setStackRoot(componentId, {
      component: {
        name: "Home",
      },
    });
  };

  return (
    <ScreenLayout hideHeaderBack={true} componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            <View style={theme.Container}>
              <View style={theme.Section}>
                <Text>
                  We are experiencing difficulties connecting to the service. Please, try again in a
                  couple of minutes.
                </Text>
              </View>
              <Button type="outline" title="Try Again" onPress={tryAgain} />
            </View>
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default ConnectionError;
