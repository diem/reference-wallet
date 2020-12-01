// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, {
  ComponentType,
  createContext,
  PropsWithChildren,
  useEffect,
  useRef,
  useState,
} from "react";
import httpStatus from "http-status-codes";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { User } from "../interfaces/user";
import SessionStorage from "../services/sessionStorage";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import { ActivityIndicator } from "react-native";

const REFRESH_TIMEOUT = 5000;

export const userContext = createContext<User | undefined>(undefined);

export const UserProvider = ({
  componentId,
  children,
}: PropsWithChildren<NavigationComponentProps>) => {
  const [user, setUser] = useState<User>();

  const timeoutRef = useRef<number>();

  async function loadUser() {
    const token = await SessionStorage.getAccessToken();
    if (!token) {
      return;
    }
    try {
      const backendClient = new BackendClient(token);
      const [newUser, newPaymentMethods] = await Promise.all([
        backendClient.getUser(),
        backendClient.getPaymentMethods(),
      ]);
      newUser.paymentMethods = newPaymentMethods;

      setUser(newUser);
      timeoutRef.current = setTimeout(loadUser, REFRESH_TIMEOUT);
    } catch (e) {
      if (e instanceof BackendError) {
        if (e.httpStatus === httpStatus.UNAUTHORIZED) {
          await SessionStorage.removeAccessToken();
          await Navigation.setStackRoot(componentId, {
            component: {
              name: "SignIn",
            },
          });
        } else {
          console.warn("Error loading user", e.httpStatus, e);
          await Navigation.setStackRoot(componentId, {
            component: {
              name: "ConnectionError",
            },
          });
        }
      } else {
        console.error(e);
      }
    }
  }

  useEffect(() => {
    loadUser();

    return () => {
      clearTimeout(timeoutRef.current!);
    };
  }, []);

  if (user) {
    return <userContext.Provider value={user} children={children} />;
  } else {
    return <ActivityIndicator size="large" />;
  }
};

export const withUserContext = (
  WrappedComponent: ComponentType<NavigationComponentProps & any>
) => (props: PropsWithChildren<NavigationComponentProps>) => (
  <UserProvider componentId={props.componentId}>
    <WrappedComponent {...props} />
  </UserProvider>
);
