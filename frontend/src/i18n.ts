// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import LocaleResources from "./locales";

i18next.use(initReactI18next).init({
  interpolation: { escapeValue: false }, // React already does escaping,
  lng: "en",
  debug: true,
  resources: LocaleResources,
});

export const Languages = Object.keys(LocaleResources);

export default i18next;
