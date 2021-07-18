// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, Modal, ModalBody, Spinner, Row, Col } from "reactstrap";
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
  redirect: () => void;
}

function PaymentConfirmationModal({
  open,
  onClose,
  redirect,
  paymentParams,
}: PaymentConfirmationProps) {
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
    if (paymentParams.demo) {
      setSubmitStatus("sending");
    } else {
      try {
        await new BackendClient().approvePayment(paymentParams.referenceId, paymentParams.isFull);
      } catch (e) {
        console.error(e);
        setSubmitStatus("fail");
      }
    }
  };

  useEffect(() => {
    if (paymentParams.demo && submitStatus === "sending") {
      setTimeout(() => {
        setSubmitStatus("success");
      }, 1000);
    }
  }, [submitStatus, paymentParams]);

  const onReject = async () => {
    // If on demo don't call the backend
    if (!paymentParams.demo) {
      await new BackendClient().rejectPayment(paymentParams.referenceId);
      setSubmitStatus("success");
    }
  };

  const humanFriendlyAmount = paymentParams.amount
    ? diemAmountToHumanFriendly(paymentParams.amount, true)
    : undefined;

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        {submitStatus === "edit" && <h4 style={{ fontWeight: 500 }}>{t("confirmation.title")}</h4>}
        {submitStatus === "fail" && (
          <h4 style={{ fontWeight: 500 }}>{t("confirmation.error_occured")}</h4>
        )}
        {submitStatus === "success" && (
          <h3 style={{ fontWeight: 500 }}>{t("confirmation.title_payment_approved")}</h3>
        )}
        {!paymentParams.isFull && (
          <div className="d-flex justify-content-center my-5">
            <Spinner color="primary" />
          </div>
        )}
        {/* sending & success case */}
        {paymentParams.isFull && (submitStatus === "edit" || submitStatus === "sending") && (
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
            <Row>
              <Col xs="1">
                <img
                  src={require("../assets/img/logo.svg")}
                  alt={t("confirmation.store_name")}
                  width={30}
                  height={30}
                />
              </Col>
              <Col>
                <h3>{paymentParams.merchantName}</h3>
              </Col>
            </Row>
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
              <small>{t("confirmation.reference_id")}</small>
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
            <>
              <Button color="black" block onClick={onConfirm}>
                {submitStatus === "sending" ? (
                  <>
                    {t("confirmation.processing")}
                    <i className="fa fa-spin fa-spinner" style={{ marginLeft: 10 }} />
                  </>
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
          </>
        )}
        {paymentParams.isFull && submitStatus === "success" && (
          <>
            <p>
              {t("confirmation.payment_approved", {
                replace: {
                  merchant: paymentParams.merchantName,
                },
              })}
            </p>
            {submitStatus === "success" && (
              <Button outline color="black" block onClick={redirect}>
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
