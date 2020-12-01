// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import ReactDatePicker from "react-native-datepicker";
import { ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";

interface DatePickerProps {
  value?: string | Date;
  placeholder?: string;
  onChange?: (dateStr: string, date: Date) => void;
  maxDate?: string | Date;
  disabled?: boolean;
}

function DatePicker({ value, placeholder, onChange, maxDate, disabled }: DatePickerProps) {
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <ReactDatePicker
          style={{ width: "100%" }}
          date={value}
          mode="date"
          disabled={disabled}
          placeholder={placeholder}
          format="YYYY-MM-DD"
          maxDate={maxDate}
          confirmBtnText="Confirm"
          cancelBtnText="Cancel"
          showIcon={false}
          customStyles={theme.DatePicker}
          onDateChange={onChange}
        />
      )}
    </ThemeConsumer>
  );
}

export default DatePicker;
