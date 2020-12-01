// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text, View } from "react-native";
import { appTheme } from "../../styles";
import { ThemeConsumer } from "react-native-elements";

interface InfoMessageProps {
  message: string;
}

function InfoMessage({ message }: InfoMessageProps) {
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={theme.InfoMessage}>
          <Text>{message}</Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default InfoMessage;
