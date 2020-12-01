// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "reactstrap";

function LegalDisclaimer({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("legal");

  return (
    <div className="container py-4 justify-content-center align-items-center d-flex flex-column h-100">
      <p className="text-justify">{t("legal_disclaimer")}</p>

      <Button color="black" className="mt-4" onClick={onClose}>
        OK
      </Button>
    </div>
  );
}

export default LegalDisclaimer;
