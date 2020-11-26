// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import ReactDatetime from "react-datetime";
import React from "react";
import { Moment } from "moment";
import "react-datetime/css/react-datetime.css";

const DATE_FORMAT = "MM/DD/YYYY";

interface DateTimeProps {
  value?: Moment | string;
  onChange?: (value: Moment | string) => void;
  placeholder: string;
  disabled?: boolean;
  invalid?: boolean;
  isValidDate?: (currentDate: Moment, selectedDate?: Moment) => boolean;
}

function DateTimePicker({
  value,
  onChange,
  placeholder,
  disabled,
  invalid,
  isValidDate,
}: DateTimeProps) {
  return (
    <ReactDatetime
      value={value}
      onChange={onChange}
      inputProps={{
        placeholder: `${placeholder} (${DATE_FORMAT})`,
        className: "form-control" + (invalid ? " is-invalid" : ""),
        disabled: disabled,
      }}
      isValidDate={isValidDate}
      closeOnSelect={true}
      timeFormat={false}
      dateFormat="MM/DD/YYYY"
    />
  );
}

export default DateTimePicker;
