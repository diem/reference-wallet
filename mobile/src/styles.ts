// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FullTheme } from "react-native-elements";
import { TextStyle, ViewStyle } from "react-native";
import { PickerStyle } from "react-native-picker-select";
import { DatePickerCustomStylesProps } from "react-native-datepicker";

interface AppTheme extends Partial<FullTheme> {
  Screen: ViewStyle;
  ScrollArea: ViewStyle;
  ScrollAreaContent: ViewStyle;
  Container: ViewStyle;
  SmallContainer: ViewStyle;
  Section: ViewStyle;
  ExampleSection: ViewStyle;
  ExampleSectionText: TextStyle;
  ErrorMessage: ViewStyle;
  InfoMessage: ViewStyle;
  InputErrorMessage: TextStyle;
  SelectDropdown: {
    selectStyle: PickerStyle;
    selectNoStyle: PickerStyle;
    selectDisabledStyle: PickerStyle;
    selectDisabledNoStyle: PickerStyle;
  };
  DatePicker: DatePickerCustomStylesProps;
  CheckBoxText: TextStyle;
  ButtonsGroup: {
    containerStyle: ViewStyle;
    buttonStyle: ViewStyle;
  };
  PrimaryLink: TextStyle;
  SmallLink: TextStyle;
  Title: TextStyle;
  SubTitle: TextStyle;
}

export const appTheme: AppTheme = {
  colors: {
    primary: "#000",
    success: "#4caf50",
    error: "#ff331f",
  },
  Header: {
    containerStyle: {
      backgroundColor: "white",
      borderTopWidth: 3,
      borderTopColor: "#6d40ed",
      borderBottomWidth: 1,
      borderBottomColor: "#e9ecef",
      height: 64,
      paddingTop: 0,
    },
  },
  Text: {
    h1Style: {
      color: "#000",
      fontSize: 22,
      fontWeight: "bold",
      marginBottom: 16,
      fontFamily: "FreeSans-Bold",
    },
    style: {
      color: "#75767f",
      lineHeight: 22,
      fontSize: 16,
      fontFamily: "FreeSans",
    },
  },
  Screen: {
    height: "100%",
  },
  ScrollArea: {
    backgroundColor: "white",
  },
  ScrollAreaContent: {
    //
  },
  Container: {
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  SmallContainer: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  Section: {
    marginBottom: 16,
  },
  ExampleSection: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: "#000",
    alignItems: "center",
  },
  ExampleSectionText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "bold",
  },
  ErrorMessage: {
    borderWidth: 1,
    borderColor: "#ff331f",
    borderRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  InfoMessage: {
    borderWidth: 1,
    borderColor: "#96a8fc",
    borderRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  Input: {
    containerStyle: {
      paddingHorizontal: 0,
      marginBottom: 0,
    },
    inputContainerStyle: {
      borderBottomWidth: 0,
      backgroundColor: "#eff1f3",
      borderRadius: 8,
    },
    inputStyle: {
      color: "#000",
      paddingVertical: 14,
      paddingHorizontal: 16,
      fontSize: 16,
      lineHeight: 18,
      minHeight: undefined,
    },
    placeholderTextColor: "#75767f",
    leftIconContainerStyle: {
      height: undefined,
      paddingLeft: 8,
      paddingRight: 0,
      marginVertical: 0,
      marginRight: 8,
    },
    rightIconContainerStyle: {
      height: undefined,
      paddingLeft: 0,
      marginVertical: 0,
      marginRight: 8,
    },
  },
  InputErrorMessage: {
    color: "#ff331f",
    fontSize: 12,
  },
  SelectDropdown: {
    selectStyle: {
      viewContainer: {
        backgroundColor: "#eff1f3",
        borderRadius: 8,
      },
      placeholder: {
        color: "#75767f",
        fontSize: 16,
        lineHeight: 18,
      },
      iconContainer: {
        top: 20,
        right: 16,
      },
      inputAndroidContainer: {
        padding: 0,
        paddingVertical: 12,
        paddingHorizontal: 16,
      },
      inputAndroid: {
        fontSize: 16,
        lineHeight: 18,
        color: "#000000",
      },
      inputIOSContainer: {
        padding: 0,
        paddingVertical: 12,
        paddingHorizontal: 16,
      },
      inputIOS: {
        fontSize: 16,
        lineHeight: 18,
        color: "#000000",
      },
    },
    selectNoStyle: {
      headlessAndroidContainer: {},
      placeholder: {
        color: "#75767f",
        fontSize: 16,
        lineHeight: 18,
      },
      iconContainer: {
        top: 20,
      },
      inputAndroid: {
        height: 48,
        fontSize: 16,
        lineHeight: 18,
        color: "#000000",
        paddingRight: 16,
      },
      inputIOS: {
        fontSize: 16,
        lineHeight: 18,
        color: "#000000",
        paddingRight: 16,
      },
    },
    selectDisabledStyle: {
      viewContainer: {
        backgroundColor: "#eff1f3",
        borderRadius: 8,
      },
      placeholder: {
        color: "#75767f",
        fontSize: 16,
        lineHeight: 18,
      },
      iconContainer: {
        top: 20,
        right: 16,
      },
      inputAndroidContainer: {
        padding: 0,
        paddingVertical: 12,
        paddingHorizontal: 16,
      },
      inputAndroid: {
        fontSize: 16,
        lineHeight: 18,
        color: "#75767f",
      },
      inputIOSContainer: {
        padding: 0,
        paddingVertical: 12,
        paddingHorizontal: 16,
      },
      inputIOS: {
        fontSize: 16,
        lineHeight: 18,
        color: "#75767f",
      },
    },
    selectDisabledNoStyle: {
      headlessAndroidContainer: {},
      placeholder: {
        color: "#75767f",
        fontSize: 16,
        lineHeight: 18,
      },
      iconContainer: {
        top: 20,
      },
      inputAndroid: {
        height: 48,
        fontSize: 16,
        lineHeight: 18,
        color: "#75767f",
        paddingRight: 16,
      },
      inputIOS: {
        fontSize: 16,
        lineHeight: 18,
        color: "#75767f",
        paddingRight: 16,
      },
    },
  },
  DatePicker: {
    dateTouchBody: {
      flexDirection: "row",
      height: "auto",
      alignItems: "center",
      justifyContent: "center",
      paddingVertical: 14,
      paddingHorizontal: 16,
      backgroundColor: "#eff1f3",
      borderRadius: 8,
    },
    dateIcon: {
      width: 32,
      height: 32,
      marginLeft: 5,
      marginRight: 5,
    },
    dateInput: {
      flex: 1,
      height: "auto",
      borderWidth: 0,
      borderColor: "#aaa",
      alignItems: "flex-start",
      justifyContent: "center",
      paddingVertical: 4,
    },
    dateText: {
      color: "#000",
      fontSize: 16,
      lineHeight: 18,
    },
    placeholderText: {
      color: "#75767f",
      fontSize: 16,
      lineHeight: 18,
    },
    datePickerCon: {
      backgroundColor: "#fff",
      height: 0,
      overflow: "hidden",
    },
    btnTextCancel: {
      color: "#666",
    },
    btnCancel: {
      left: 0,
    },
    btnConfirm: {
      right: 0,
    },
    datePicker: {
      marginTop: 42,
      borderTopColor: "#ccc",
      borderTopWidth: 1,
    },
    disabled: {
      backgroundColor: "transparent",
      opacity: 0.5,
    },
  },
  CheckBox: {
    wrapperStyle: {
      margin: 0,
      marginVertical: 8,
    },
    containerStyle: {
      margin: 0,
      padding: 0,
      marginLeft: 0,
      marginRight: 0,
      borderWidth: 0,
      backgroundColor: "none",
    },
  },
  CheckBoxText: {
    marginLeft: 8,
  },
  ButtonsGroup: {
    containerStyle: {
      flexDirection: "row",
      justifyContent: "space-evenly",
      marginHorizontal: -8,
    },
    buttonStyle: {
      flexGrow: 1,
      flexBasis: 0,
      marginHorizontal: 8,
    },
  },
  Button: {
    buttonStyle: {
      margin: 0,
      paddingVertical: 8,
      paddingHorizontal: 8,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 0.5,
    },
    titleStyle: {
      fontSize: 16,
      lineHeight: 18,
      fontWeight: "bold",
      paddingTop: 0,
      paddingBottom: 0,
    },
    iconContainerStyle: {
      marginHorizontal: 0,
    },
    icon: {
      iconStyle: {
        color: "white",
      },
    },
  },
  PrimaryLink: {
    color: "#506efa",
  },
  SmallLink: {
    fontSize: 12,
    color: "#75767F",
  },
  Title: {
    fontWeight: "bold",
    fontSize: 28,
    lineHeight: 28,
    color: "#000000",
  },
  SubTitle: {
    fontSize: 20,
    lineHeight: 20,
  },
};
