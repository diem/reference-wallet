// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { ReactElement, useContext } from "react";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { Transaction } from "../interfaces/transaction";
import {
  fiatToDiemHumanFriendly,
  diemAmountToFloat,
  diemAmountToHumanFriendly,
} from "../utils/amount-precision";
import { classNames } from "../utils/class-names";

const STATUS_COLORS = {
  completed: "success",
  pending: "warning",
  canceled: "danger",
};

interface TransactionsListProps {
  transactions: Transaction[];
  onSelect?: (transaction: Transaction) => void;
  bottom?: ReactElement;
}

function TransactionsList({ transactions, onSelect, bottom }: TransactionsListProps) {
  const { t } = useTranslation("transaction");
  const [settings] = useContext(settingsContext)!;

  const itemStyles = {
    "list-group-item": true,
    "list-group-item-action": !!onSelect,
    "cursor-pointer": !!onSelect,
  };

  const bottomStyles = {
    "list-group-item": true,
    "text-center": true,
  };

  return (
    <ul className="list-group my-4">
      {transactions.map((transaction) => {
        const currency = settings.currencies[transaction.currency];
        const fiatCurrency = settings.fiatCurrencies[settings.defaultFiatCurrencyCode!];
        const exchangeRate = currency.rates[settings.defaultFiatCurrencyCode!];

        return (
          <li
            className={classNames(itemStyles)}
            key={transaction.id}
            onClick={() => onSelect && onSelect(transaction)}
          >
            <div className="d-flex">
              {transaction.direction === "received" && (
                <>
                  <span className="text-black mr-4 overflow-auto">
                    <strong className="text-capitalize-first">{t(transaction.direction)}</strong>{" "}
                    {t("from")} <span>{transaction.source.full_addr}</span>
                  </span>

                  <span className="text-black ml-auto text-nowrap">
                    {diemAmountToHumanFriendly(transaction.amount, true)} {currency.sign}
                  </span>
                </>
              )}

              {transaction.direction === "sent" && (
                <>
                  <span className="text-black mr-4 overflow-auto">
                    <strong className="text-capitalize-first">{t(transaction.direction)}</strong>{" "}
                    {t("to")} <span>{transaction.destination.full_addr}</span>
                  </span>

                  <span className="text-black ml-auto text-nowrap">
                    - {diemAmountToHumanFriendly(transaction.amount, true)} {currency.sign}
                  </span>
                </>
              )}
            </div>
            <div className="d-flex">
              <span className="small">
                <i className={`fa fa-circle text-${STATUS_COLORS[transaction.status]}`} />{" "}
                {new Date(transaction.timestamp).toLocaleDateString()}
              </span>
              <span className="small ml-auto">
                {fiatCurrency.sign}
                {fiatToDiemHumanFriendly(
                  diemAmountToFloat(transaction.amount) * exchangeRate,
                  true
                )}{" "}
                {fiatCurrency.symbol}
              </span>
            </div>
          </li>
        );
      })}
      {bottom && <li className={classNames(bottomStyles)}>{bottom}</li>}
    </ul>
  );
}

export default TransactionsList;
