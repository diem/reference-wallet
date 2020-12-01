// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { withUserContext } from "../../contexts/user";
import { withAccountContext } from "../../contexts/account";
import ScreenLayout from "../../components/ScreenLayout";
import { appTheme } from "../../styles";
import { withRatesContext } from "../../contexts/rates";
import QRCodeScanner from "react-native-qrcode-scanner";
import { TouchableOpacity } from "react-native";

interface SendScanQRProps {
  callback: (data: any) => void;
}

function SendScanQR({ callback, componentId }: SendScanQRProps & NavigationComponentProps) {
  const { t } = useTranslation("send");

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <QRCodeScanner
            onRead={(e) => {
              callback(e.data);
              Navigation.pop(componentId);
            }}
            bottomViewStyle={{ padding: 16 }}
            bottomContent={
              <TouchableOpacity
                onPress={() => {
                  Navigation.pop(componentId);
                }}
              >
                <Text>Back</Text>
              </TouchableOpacity>
            }
          />
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withRatesContext(withAccountContext(withUserContext(SendScanQR)));
