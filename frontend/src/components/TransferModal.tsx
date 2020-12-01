// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Button, Modal, ModalBody } from "reactstrap";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Currency } from "../interfaces/currencies";
import Deposit from "./Transfer/Deposit";
import Withdraw from "./Transfer/Withdraw";
import Convert from "./Transfer/Convert";
import CloseButton from "./CloseButton";

interface TransferModalProps {
  currency?: Currency;
  open: boolean;
  onClose: () => void;
}

function TransferModal({ open, onClose, currency }: TransferModalProps) {
  const { t } = useTranslation("transfer");

  const [mode, setMode] = useState<"deposit" | "withdraw" | "convert" | undefined>();

  function onModalClose() {
    setMode(undefined);
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody>
        <CloseButton onClick={onModalClose} />
        {!mode && (
          <>
            <h3>{t("title")}</h3>
            <Button outline color="black" block onClick={() => setMode("deposit")}>
              {t("modes.deposit")}
            </Button>
            <Button outline color="black" block onClick={() => setMode("withdraw")}>
              {t("modes.withdraw")}
            </Button>
            <Button outline color="black" block onClick={() => setMode("convert")}>
              {t("modes.convert")}
            </Button>
          </>
        )}
        {mode === "deposit" && <Deposit initialCurrency={currency} onComplete={onModalClose} />}
        {mode === "withdraw" && <Withdraw initialCurrency={currency} onComplete={onModalClose} />}
        {mode === "convert" && <Convert initialCurrency={currency} onComplete={onModalClose} />}
      </ModalBody>
    </Modal>
  );
}

export default TransferModal;
