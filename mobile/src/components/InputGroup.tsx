// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { PropsWithChildren } from "react";
import { View } from "react-native";
import { ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";

function InputGroup({ children }: PropsWithChildren<any>) {
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={theme.InputGroup.containerStyle}>
          <View style={theme.InputGroup.inputContainerStyle} children={children} />
        </View>
      )}
    </ThemeConsumer>
  );
}

export default InputGroup;
