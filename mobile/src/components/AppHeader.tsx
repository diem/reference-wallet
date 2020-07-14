// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Header } from "react-native-elements";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { userContext } from "../contexts/user";
import NetworkIndicator from "./NetworkIndicator";
import Logo from "../assets/logo.svg";
import Gears from "../assets/gears.svg";
import { TouchableOpacity } from "react-native";

function AppHeader({ componentId }: NavigationComponentProps) {
  const user = useContext(userContext);

  async function goToRoot() {
    await Navigation.popToRoot(componentId);
  }

  async function goToSettings() {
    await Navigation.push(componentId, {
      component: {
        name: "Settings",
      },
    });
  }

  return (
    <Header
      leftComponent={<NetworkIndicator />}
      centerComponent={
        <TouchableOpacity onPress={goToRoot}>
          <Logo style={{ margin: 8 }} />
        </TouchableOpacity>
      }
      rightComponent={user && <Gears onPress={goToSettings} />}
    />
  );
}

export default AppHeader;
