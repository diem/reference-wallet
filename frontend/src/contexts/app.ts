// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { createContext, Dispatch, SetStateAction } from "react";
import { AppSettings } from "../interfaces/settings";

type SettingsContext = [AppSettings, Dispatch<SetStateAction<AppSettings>>];

export const settingsContext = createContext<SettingsContext | undefined>(undefined);
