// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, {
  ComponentProps,
  ComponentType,
  createContext,
  PropsWithChildren,
  useEffect,
  useRef,
  useState,
} from "react";
import { NavigationComponentProps } from "react-native-navigation";
import { Account } from "../interfaces/account";
import SessionStorage from "../services/sessionStorage";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";

const REFRESH_TIMEOUT = 5000;

export const accountContext = createContext<Account | undefined>(undefined);

export const AccountProvider = ({ children }: PropsWithChildren<any>) => {
  const [account, setAccount] = useState<Account>();

  const timeoutRef = useRef<number>();

  async function loadAccount() {
    const token = await SessionStorage.getAccessToken();
    if (!token) {
      return;
    }
    try {
      const backendClient = new BackendClient(token);
      setAccount(await backendClient.getAccount());
      timeoutRef.current = setTimeout(loadAccount, REFRESH_TIMEOUT);
    } catch (e) {
      if (e instanceof BackendError) {
        console.warn("Error loading account", e.httpStatus, e);
      } else {
        console.error(e);
      }
    }
  }

  useEffect(() => {
    loadAccount();

    return () => {
      clearTimeout(timeoutRef.current!);
    };
  }, []);

  return <accountContext.Provider value={account} children={children} />;
};

export const withAccountContext = (
  WrappedComponent: ComponentType<NavigationComponentProps & any>
) => (props: ComponentProps<any>) => (
  <AccountProvider>
    <WrappedComponent {...props} />
  </AccountProvider>
);
