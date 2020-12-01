// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { ThemeConsumer } from "react-native-elements";
import RNPickerSelect, { PickerStyle } from "react-native-picker-select";
import { appTheme } from "../styles";
// @ts-ignore
import Chevron from "../assets/chevron.svg";

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
      {({ theme }) => {
        let pickerStyle: PickerStyle;
        if (disableStyles) {
          pickerStyle = disabled
            ? theme.SelectDropdown.selectDisabledNoStyle
            : theme.SelectDropdown.selectNoStyle;
        } else {
          pickerStyle = disabled
            ? theme.SelectDropdown.selectDisabledStyle
            : theme.SelectDropdown.selectStyle;
        }
        return (
          <>
            <RNPickerSelect
              value={value}
              disabled={disabled}
              placeholder={label ? { label, value: undefined } : undefined}
              style={pickerStyle}
              useNativeAndroidPickerStyle={!disableStyles}
              onValueChange={(key) => onChange && onChange(key as keyof V)}
              items={optionsList.map((option) => ({
                label: options[option as keyof V] as string,
                value: option,
              }))}
              Icon={() => <Chevron />}
            />
          </>
        );
      }}
    </ThemeConsumer>
  );
}

export default SelectDropdown;
