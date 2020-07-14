// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";

function VerifyingMessage() {
  const { t } = useTranslation("layout");

  return (
    <section className="slim-section m-auto">
      <h1 className="h3">{t("verification_pending.title")}</h1>
      <p>{t("verification_pending.description")}</p>
    </section>
  );
}

export default VerifyingMessage;
