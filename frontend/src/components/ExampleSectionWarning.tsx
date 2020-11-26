// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";

const ExampleSectionWarning = () => {
  const { t } = useTranslation("legal");

  return (
    <div className="p-2 bg-black text-white text-center text-uppercase small">
      {t("example_section_warning")}
    </div>
  );
};

export default ExampleSectionWarning;
