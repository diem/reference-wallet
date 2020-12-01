// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Modal, ModalBody } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import ExplorerLink from "./ExplorerLink";
import { Transaction } from "../interfaces/transaction";
import CloseButton from "./CloseButton";
import {
  fiatToDiemHumanFriendly,
  diemAmountToFloat,
  diemAmountToHumanFriendly,
} from "../utils/amount-precision";

const STATUS_COLORS = {
  completed: "success",
  pending: "warning",
  canceled: "danger",
};

interface TransactionModalProps {
  open: boolean;
  onClose: () => void;
  transaction?: Transaction;
}

function TransactionModal({ open, onClose, transaction }: TransactionModalProps) {
  const { t } = useTranslation("transaction");

  const [settings] = useContext(settingsContext)!;

  if (!transaction) {
    return null;
  }

  const currency = settings.currencies[transaction.currency];
  const fiatCurrency = settings.fiatCurrencies[settings.defaultFiatCurrencyCode!];

  const exchangeRate = currency.rates[settings.defaultFiatCurrencyCode!] || 0;

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <div className="text-center">
          <div className="h2 text-capitalize-first">{t(transaction.direction)}</div>

          <h2 className="h2 m-0">
            {diemAmountToHumanFriendly(transaction.amount, true)} {currency.sign}
          </h2>

          <div>
            {t("price")} {fiatCurrency.sign}
            {fiatToDiemHumanFriendly(
              diemAmountToFloat(transaction.amount) * exchangeRate,
              true
            )}{" "}
            {fiatCurrency.symbol}
          </div>
        </div>

        <div className="mt-4">
          {t("date")}
          <div className="text-black">{new Date(transaction.timestamp).toLocaleString()}</div>
        </div>

        {transaction.direction === "sent" && (
          <div className="mt-4">
            {t("sent_to")}
            <div>
              <span className="text-black" title={transaction.destination.user_id}>
                {transaction.destination.full_addr}
              </span>
            </div>
          </div>
        )}
        {transaction.direction === "received" && (
          <div className="mt-4">
            {t("sent_from")}
            <div>
              <span className="text-black" title={transaction.source.user_id}>
                {transaction.source.full_addr}
              </span>
            </div>
          </div>
        )}

        <div className="mt-4">
          {t("status")}
          <div>
            <i className={`fa fa-circle text-${STATUS_COLORS[transaction.status]}`} />{" "}
            <span className="text-black text-capitalize" title={transaction.status}>
              {transaction.status}
            </span>
          </div>
        </div>

        <div className="mt-4">
          {t("tx_id")}
          <div>
            {transaction.is_internal && (
              <span className="text-black text-capitalize">{t("internal")}</span>
            )}
            {!transaction.is_internal &&
              (transaction.blockchain_tx && transaction.blockchain_tx.version ? (
                <ExplorerLink blockchainTx={transaction.blockchain_tx!} />
              ) : (
                <span className="text-black text-capitalize">{t("not_available")}</span>
              ))}
          </div>
        </div>
      </ModalBody>
    </Modal>
  );
}

export default TransactionModal;
