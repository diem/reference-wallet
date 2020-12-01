// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Modal, ModalBody } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";
import { Currency } from "../../interfaces/currencies";
import BackendClient from "../../services/backendClient";
import { Send } from "./interfaces";
import SendForm from "./SendForm";
import SendReview from "./SendReview";
import CloseButton from "../CloseButton";
import { diemAmountFromFloat } from "../../utils/amount-precision";
import ErrorMessage from "../Messages/ErrorMessage";
import SuccessMessage from "../Messages/SuccessMessage";
import { BackendError } from "../../services/errors";

interface SendModalProps {
  initialCurrency?: Currency;
  open: boolean;
  onClose: () => void;
}

function SendModal({ open, onClose, initialCurrency }: SendModalProps) {
  const { t } = useTranslation("send");
  const [settings] = useContext(settingsContext)!;

  const [data, setData] = useState<Send>({
    currency: initialCurrency,
    fiatCurrency: settings.defaultFiatCurrencyCode!,
  });

  const [reviewing, setReviewing] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [errorMessage, setErrorMessage] = useState<string>();
  const [sentTransactionID, setSentTransactionID] = useState<number>();

  useEffect(() => {
    async function refreshUser() {
      try {
        await new BackendClient().refreshUser();
      } catch (e) {
        console.error(e);
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();
  }, []);

  if (!settings.account) {
    return null;
  }

  function onModalClose() {
    setReviewing(false);
    setData({
      currency: initialCurrency,
      fiatCurrency: settings.defaultFiatCurrencyCode!,
    });
    setSentTransactionID(undefined);
    setSubmitStatus("edit");
    setErrorMessage(undefined);
    onClose();
  }

  async function sendTransaction() {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const backendClient = new BackendClient();
      const transaction = await backendClient.createTransaction(
        data.currency!,
        diemAmountFromFloat(data.amount!),
        data.address!
      );

      setSentTransactionID(transaction.id);
      setSubmitStatus("success");
      await backendClient.refreshUser();
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody>
        <CloseButton onClick={onModalClose} />
        {errorMessage && <ErrorMessage message={errorMessage} />}
        {submitStatus === "success" && <SuccessMessage message={t("success_message")} />}

        {reviewing ? (
          <SendReview
            data={data as Required<Send>}
            submitting={submitStatus === "sending"}
            submitted={submitStatus === "success"}
            onBack={() => {
              setReviewing(false);
              setErrorMessage(undefined);
            }}
            onConfirm={sendTransaction}
            onComplete={onModalClose}
          />
        ) : (
          <SendForm
            value={data}
            onSubmit={(newData) => {
              setData(newData);
              setReviewing(true);
            }}
          />
        )}
      </ModalBody>
    </Modal>
  );
}

export default SendModal;
