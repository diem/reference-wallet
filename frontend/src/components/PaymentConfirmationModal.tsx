// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import { Trans, useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { Currency } from "../interfaces/currencies";
import { diemAmountToHumanFriendly } from "../utils/amount-precision";
import { PaymentParams } from "../utils/payment-params";
import CloseButton from "./CloseButton";
import BackendClient from "../services/backendClient";
import ErrorMessage from "./Messages/ErrorMessage";

interface PaymentConfirmationProps {
  open: boolean;
  onClose: () => void;
  paymentParams: PaymentParams;
}

function PaymentConfirmationModal({ open, onClose, paymentParams }: PaymentConfirmationProps) {
  const { t } = useTranslation("send");

  const [settings] = useContext(settingsContext)!;

  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const currency = settings.currencies[paymentParams.currency];

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

  const onConfirm = () => {};
  const onReject = () => {};
  const onComplete = () => {};

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />

        {errorMessage && <ErrorMessage message={errorMessage} />}

        <h3>{t("review.title")}</h3>

        <div>
          <small>{t("review.amount")}</small>
          <p className="text-black">
            {diemAmountToHumanFriendly(paymentParams.amount, true)} {currency.sign}
          </p>
        </div>

        <div>
          <small>{t("review.amount")}</small>
          <p className="text-black">{paymentParams.merchantName}</p>
        </div>

        <div>
          <small>{t("review.amount")}</small>
          <p className="text-black">{paymentParams.referenceId}</p>
        </div>

        <div>
          <small>{t("review.amount")}</small>
          <p className="text-black">{paymentParams.vaspAddress}</p>
        </div>

        <div>
          <small>{t("review.amount")}</small>
          <p className="text-black">{paymentParams.expiration.toLocaleString()}</p>
        </div>

        {submitStatus !== "success" && (
          <>
            <Button color="black" block onClick={onConfirm} disabled={submitStatus === "sending"}>
              {submitStatus === "sending" ? (
                <i className="fa fa-spin fa-spinner" />
              ) : (
                t("review.confirm")
              )}
            </Button>
            <Button
              outline
              color="black"
              block
              onClick={onReject}
              disabled={submitStatus === "sending"}
            >
              {t("review.back")}
            </Button>
          </>
        )}
        {submitStatus === "success" && (
          <Button outline color="black" block onClick={onComplete}>
            {t("review.done")}
          </Button>
        )}
      </ModalBody>
    </Modal>
  );
}

export default PaymentConfirmationModal;
