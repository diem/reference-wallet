// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from "react-i18next";
import React from "react";
import { Button } from "reactstrap";

interface ActionsProps {
  onSendClick?: () => void;
  onRequestClick?: () => void;
  onTransferClick?: () => void;
}

function Actions({ onSendClick, onRequestClick, onTransferClick }: ActionsProps) {
  const { t } = useTranslation("layout");

  return (
    <>
      <Button color="black" outline disabled={!onSendClick} onClick={onSendClick}>
        {t("actions.send")}
      </Button>
      <Button
        color="black"
        outline
        disabled={!onRequestClick}
        onClick={onRequestClick}
        className="mx-2 mx-sm-4"
      >
        {t("actions.request")}
      </Button>
      <Button color="black" outline disabled={!onTransferClick} onClick={onTransferClick}>
        {t("actions.transfer")}
      </Button>
    </>
  );
}

export default Actions;
