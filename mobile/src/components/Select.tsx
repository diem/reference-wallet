// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { ThemeConsumer } from "react-native-elements";
import RNPickerSelect from "react-native-picker-select";

import { appTheme } from "../styles";

type Values = Record<string | number, string | undefined> | Array<string>;

interface SelectDropdownProps<V extends Values> {
  label?: string;
  options: V;
  value?: keyof V;
  onChange?: (val: keyof V) => void;
  disabled?: boolean;
  disableStyles?: boolean;
}

function SelectDropdown<V extends Values = {}>({
  label,
  options,
  value,
  onChange,
  disabled,
  disableStyles,
}: SelectDropdownProps<V>) {
  let optionsList: (string | number)[];
  if (options instanceof Array) {
    optionsList = Array.apply(null, Array(options.length)).map((x, i) => i);
  } else {
    optionsList = Object.keys(options);
  }

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <RNPickerSelect
            value={value}
            disabled={disabled}
            placeholder={label ? { label, value: undefined } : undefined}
            style={
              disableStyles ? theme.SelectDropdown.selectNoStyle : theme.SelectDropdown.selectStyle
            }
            useNativeAndroidPickerStyle={!disableStyles}
            onValueChange={(key) => onChange && onChange(key as keyof V)}
            items={optionsList.map((option) => ({
              label: options[option as keyof V] as string,
              value: option,
            }))}
          />
        </>
      )}
    </ThemeConsumer>
  );
}

export default SelectDropdown;
