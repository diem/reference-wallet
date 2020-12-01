// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { createRef, RefObject } from "react";
import { DropdownItem, DropdownMenu, DropdownToggle, UncontrolledDropdown } from "reactstrap";
import { classNames } from "../../utils/class-names";

interface SelectDropdownProps<T extends object> {
  label?: string;
  options: T;
  value?: keyof T;
  onChange?: (val: keyof T) => void;
  dropdownAction?: React.ReactNode;
  textOverflow?: boolean;
  invalid?: boolean;
  disabled?: boolean;

  addonType?: boolean | "prepend" | "append";
}

function SelectDropdown<T extends object = object>({
  label,
  options,
  value,
  onChange,
  dropdownAction,
  textOverflow,
  invalid,
  disabled,
  ...props
}: SelectDropdownProps<T>) {
  let optionsList: (string | number)[];
  if (options instanceof Array) {
    optionsList = Array.apply(null, Array(options.length)).map((x, i) => i);
  } else {
    optionsList = Object.keys(options);
  }

  const hasValue = value !== undefined;

  const toggleStyles = {
    "font-weight-normal": true,
    "border-0": true,
    "btn-block": true,
    "d-inline-flex": true,
    "align-items-center": true,
    "justify-content-between": true,
    "is-invalid": !!invalid,
  };

  const optionStyles = {
    "cursor-pointer": true,
    "text-capitalize-first": true,
    "overflow-auto": !!textOverflow,
    "text-truncate": !textOverflow,
  };

  const labelStyles = {
    "text-capitalize-first": true,
    "overflow-auto": !!textOverflow,
    "text-truncate": !textOverflow,
    "text-black": hasValue,
  };

  const refs: Record<string, RefObject<any>> = optionsList.reduce((acc, opt) => {
    acc[opt] = createRef();
    return acc;
  }, {});

  const scrollValueToView = () => {
    if (value) {
      const ref = refs[value as string];
      if (ref) {
        setTimeout(() => {
          if (ref.current) {
            ref.current.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }
        }, 100);
      }
    }
  };

  return (
    <UncontrolledDropdown disabled={disabled} {...props} onToggle={scrollValueToView}>
      <DropdownToggle
        disabled={disabled}
        color="default"
        className={classNames(toggleStyles)}
        caret
      >
        <span className={classNames(labelStyles)}>{hasValue ? options[value!] : label}</span>
      </DropdownToggle>
      <DropdownMenu className="w-100 mw-100 scrollable-menu">
        {optionsList.map((key) => {
          return (
            <DropdownItem
              key={key}
              tag={(props) => <div {...props} ref={refs[key as string]} />}
              className={classNames({ ...optionStyles, active: key === value })}
              onClick={() => onChange && onChange(key as keyof T)}
            >
              {options[key]}
            </DropdownItem>
          );
        })}
        {dropdownAction && <DropdownItem>{dropdownAction}</DropdownItem>}
      </DropdownMenu>
    </UncontrolledDropdown>
  );
}

export default SelectDropdown;
