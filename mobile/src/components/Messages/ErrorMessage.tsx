// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text, View } from "react-native";
import { appTheme } from "../../styles";
import { ThemeConsumer } from "react-native-elements";

interface ErrorMessageProps {
  message: string;
}

function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={theme.ErrorMessage}>
          <Text>{message}</Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default ErrorMessage;
