// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";

interface InputErrorMessageProps {
  message: string;
}

function InputErrorMessage({ message }: InputErrorMessageProps) {
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => <Text style={theme.InputErrorMessage}>{message}</Text>}
    </ThemeConsumer>
  );
}

export default InputErrorMessage;
