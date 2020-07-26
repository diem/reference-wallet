import React from "react";
import ReactDatePicker from "react-native-datepicker";

interface DatePickerProps {
  value?: string | Date;
  onChange?: (dateStr: string, date: Date) => void;
}

function DatePicker({ value, onChange }: DatePickerProps) {
  return (
    <ReactDatePicker
      style={{ width: 200 }}
      date={value}
      mode="date"
      placeholder="select date"
      format="YYYY-MM-DD"
      minDate="2016-05-01"
      maxDate="2016-06-01"
      confirmBtnText="Confirm"
      cancelBtnText="Cancel"
      customStyles={{
        dateIcon: {
          position: "absolute",
          left: 0,
          top: 4,
          marginLeft: 0,
        },
        dateInput: {
          marginLeft: 36,
        },
        // ... You can check the source to find the other keys.
      }}
      onDateChange={onChange}
    />
  );
}

export default DatePicker;
