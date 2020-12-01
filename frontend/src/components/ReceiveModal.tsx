// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, FormGroup, FormText, Modal, ModalBody } from "reactstrap";
import QRCode from "qrcode.react";
import { Trans, useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { Currency } from "../interfaces/currencies";
import SelectDropdown from "./select";
import CloseButton from "./CloseButton";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import ErrorMessage from "./Messages/ErrorMessage";
import { currenciesWithBalanceOptions } from "../utils/dropdown-options";
import { ADDR_PROTOCOL_PREFIX } from "../interfaces/blockchain";

interface ReceiveModalProps {
  open: boolean;
  onClose: () => void;
  currency?: Currency;
}

function ReceiveModal({ open, onClose, currency }: ReceiveModalProps) {
  const { t } = useTranslation("receive");

  const [settings] = useContext(settingsContext)!;

  const [selectedCurrency, setSelectedCurrency] = useState<Currency | undefined>(currency);
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [receivingAddress, setReceivingAddress] = useState<string | undefined>();
  const [receivingAddressWithIntents, setReceivingAddressWithIntents] = useState<
    string | undefined
  >();
  const [copied, setCopied] = useState<boolean>(false);

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

  async function fetchReceivingAddress(currency: Currency) {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      let recvAddress = receivingAddress;
      if (receivingAddress === undefined) {
        recvAddress = await new BackendClient().createReceivingAddress();
        setReceivingAddress(recvAddress);
      }
      setReceivingAddressWithIntents(`${ADDR_PROTOCOL_PREFIX}${recvAddress}?c=${currency}`);
      setSubmitStatus("success");
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

  useEffect(() => {
    if (selectedCurrency) {
      // noinspection JSIgnoredPromiseFromCall
      fetchReceivingAddress(selectedCurrency);
    }
  }, [selectedCurrency]);

  async function copy() {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(receivingAddressWithIntents!);
    } else {
      const listener = (event: ClipboardEvent) => {
        event.clipboardData!.setData("text/plain", receivingAddressWithIntents!);
        event.preventDefault();
        document.removeEventListener("copy", listener, true);
      };
      document.addEventListener("copy", listener, true);
      document.execCommand("copy");
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />

        {errorMessage && <ErrorMessage message={errorMessage} />}

        <h3>{t("headline")}</h3>
        <FormGroup>
          <FormText>{t("currency_label")}</FormText>
          <SelectDropdown
            label={t("currency")}
            options={currenciesWithBalanceOptions(settings.currencies, settings.account!.balances)}
            value={selectedCurrency}
            onChange={(val) => setSelectedCurrency(val)}
          />
        </FormGroup>
        {selectedCurrency && (
          <>
            <p>{t("text")}</p>
            <div className="text-center">
              {receivingAddressWithIntents && (
                <QRCode
                  value={receivingAddressWithIntents}
                  imageSettings={{
                    src: require("assets/img/logo.svg"),
                    height: 16,
                    width: 16,
                    excavate: true,
                  }}
                />
              )}
            </div>
            <div className="text-center my-4 font-weight-bold text-break small">
              <code>{receivingAddressWithIntents}</code>
            </div>
            <Button color="black" block onClick={copy}>
              {copied ? (
                <Trans t={t} i18nKey="copied">
                  Copied <i className="fa fa-check" />
                </Trans>
              ) : (
                <Trans t={t} i18nKey="copy">
                  Copy Address
                </Trans>
              )}
            </Button>
          </>
        )}
      </ModalBody>
    </Modal>
  );
}

export default ReceiveModal;
