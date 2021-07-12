// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, Modal, ModalBody, Spinner } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { diemAmountToHumanFriendly } from "../utils/amount-precision";
import { PaymentParams } from "../utils/payment-params";
import CloseButton from "./CloseButton";
import BackendClient from "../services/backendClient";

interface PaymentConfirmationProps {
  open: boolean;
  onClose: () => void;
  paymentParams: PaymentParams;
}

function PaymentConfirmationModal({ open, onClose, paymentParams }: PaymentConfirmationProps) {
  const { t } = useTranslation("payment");

  const [settings] = useContext(settingsContext)!;

  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");

  const currency = paymentParams.currency ? settings.currencies[paymentParams.currency] : undefined;

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

  const onConfirm = async () => {
    await new BackendClient().approvePayment(paymentParams.referenceId, paymentParams.isFull);
    setSubmitStatus("success");
  };
  const onReject = async () => {
    await new BackendClient().rejectPayment(paymentParams.referenceId);
    setSubmitStatus("success");
  };

  const humanFriendlyAmount = paymentParams.amount
    ? diemAmountToHumanFriendly(paymentParams.amount, true)
    : undefined;

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <h3>{t("confirmation.title")}</h3>
        {!paymentParams.isFull && (
          <div className="d-flex justify-content-center my-5">
            <Spinner color="primary" />
          </div>
        )}
        {paymentParams.isFull && (
          <>
            <p>
              {t("confirmation.summary", {
                replace: {
                  amount: humanFriendlyAmount,
                  currency: currency.sign,
                  merchant: paymentParams.merchantName,
                },
              })}
            </p>

            <div>
              <small>{t("confirmation.amount")}</small>
              <p className="text-black">
                {humanFriendlyAmount} {currency.sign}
              </p>
            </div>

            <div>
              <small>{t("confirmation.merchant")}</small>
              <p className="text-black">{paymentParams.merchantName}</p>
            </div>

            <div>
              <small>Reference ID</small>
              <p className="text-black">{paymentParams.referenceId}</p>
            </div>

            <div>
              <small>{t("confirmation.receiver")}</small>
              <p className="text-black">{paymentParams.vaspAddress}</p>
            </div>

            {paymentParams.expiration && (
              <div>
                <small>{t("confirmation.expiration")}</small>
                <p className="text-black">{paymentParams.expiration.toLocaleString()}</p>
              </div>
            )}

            {submitStatus !== "success" && (
              <>
                <Button
                  color="black"
                  block
                  onClick={onConfirm}
                  disabled={submitStatus === "sending"}
                >
                  {submitStatus === "sending" ? (
                    <i className="fa fa-spin fa-spinner" />
                  ) : (
                    t("confirmation.approve")
                  )}
                </Button>
                <Button
                  outline
                  color="black"
                  block
                  onClick={onReject}
                  disabled={submitStatus === "sending"}
                >
                  {t("confirmation.reject")}
                </Button>
              </>
            )}
            {submitStatus === "success" && (
              <Button outline color="black" block onClick={onClose}>
                {t("confirmation.close")}
              </Button>
            )}
          </>
        )}
      </ModalBody>
    </Modal>
  );
}

export default PaymentConfirmationModal;
