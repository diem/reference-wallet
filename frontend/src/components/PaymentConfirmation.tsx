// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useHistory } from "react-router-dom";
import { Alert } from "reactstrap";
import { PaymentParams } from "../utils/payment-params";
import PaymentConfirmationModal from "./PaymentConfirmationModal";
import BackendClient from "../services/backendClient";

/**
 * Displays the payment confirmation dialog if there are payment details in the query string
 * part of the current URL. If no query string, does nothing; if wrong query string, shows
 * error alert.
 */
function PaymentConfirmation() {
  const [showError, setShowError] = useState<boolean>(false);

  // All flows end eventually with redirection to the home page, without the query string
  const history = useHistory();
  const onPaymentRequestHandlingComplete = () => {
    setShowError(false);
    history.push("/");
  };

  // Only if the query string changes, recalculate the payment params
  const queryString = useLocation().search;
  let paymentParamsFromUrl: PaymentParams | undefined = useMemo(() => {
    try {
      if (queryString) {
        return PaymentParams.fromUrlQueryString(queryString);
      }
    } catch (e) {
      setShowError(true);
    }
  }, [queryString]);

  const [paymentParams, setPaymentParams] = useState(paymentParamsFromUrl);

  useEffect(() => {
    const addPaymentCommand = async () => {
      try {
        if (paymentParams) {
          let backendClient = new BackendClient();
          await backendClient.addPaymentCommand(paymentParams);

          if (!paymentParams.isFull) {
            let payment_details;

            while (!payment_details) {
              payment_details = await backendClient.getPaymentDetails(paymentParams.referenceId);
            }

            setPaymentParams(PaymentParams.fromPaymentDetails(payment_details));
          }
        }
      } catch (e) {
        console.error(e);
      }
    };

    // noinspection JSIgnoredPromiseFromCall
    addPaymentCommand();
  }, [paymentParams]);

  return (
    <>
      <Alert
        color="danger"
        isOpen={showError}
        toggle={onPaymentRequestHandlingComplete}
        fade={false}
        className="my-5"
      >
        Invalid payment request.
      </Alert>

      {!!paymentParams && paymentParams.isFull && (
        <PaymentConfirmationModal
          open={!!paymentParams}
          paymentParams={paymentParams}
          onClose={onPaymentRequestHandlingComplete}
        />
      )}
    </>
  );
}

export default PaymentConfirmation;
