// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Col, Container, Row } from "reactstrap";
import { settingsContext } from "../contexts/app";
import BackendClient from "../services/backendClient";
import { Currency } from "../interfaces/currencies";
import { Transaction, TransactionDirection } from "../interfaces/transaction";
import TransactionsList from "../components/TransactionsList";
import TransactionModal from "../components/TransactionModal";
import Breadcrumbs from "../components/Breadcrumbs";
import { useTranslation } from "react-i18next";
import SelectDropdown from "../components/select";
import {
  getCurrenciesOptionsMap,
  transactionSortingOptions,
  transactionDirectionsOptions,
} from "../utils/dropdown-options";
import TestnetWarning from "../components/TestnetWarning";

const REFRESH_TRANSACTIONS_INTERVAL = 3000;

function Transactions() {
  const { t } = useTranslation("layout");
  const [settings] = useContext(settingsContext)!;
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionModal, setTransactionModal] = useState<Transaction>();

  const [currency, setCurrency] = useState<Currency>();
  const [direction, setDirection] = useState<TransactionDirection>();
  const [sorting, setSorting] = useState<string>("date_desc");

  let refreshTransactions = true;

  const fetchTransactions = async () => {
    try {
      if (refreshTransactions) {
        setTransactions(await new BackendClient().getTransactions(currency, direction, sorting));
        setTimeout(fetchTransactions, REFRESH_TRANSACTIONS_INTERVAL);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    try {
      // noinspection JSIgnoredPromiseFromCall
      new BackendClient().refreshUser();
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    // noinspection JSIgnoredPromiseFromCall
    fetchTransactions();

    return () => {
      refreshTransactions = false;
    };
  }, [currency, direction, sorting]);

  return (
    <>
      <TestnetWarning />

      <Breadcrumbs pageName={t("all_transactions")} />
      <Container className="py-5">
        <section>
          <h2 className="h5 font-weight-normal text-body">{t("all_transactions")}</h2>

          <Row>
            <Col md={4} className="mb-2 mb-md-0">
              <SelectDropdown
                label={t("all_currencies")}
                value={currency}
                options={getCurrenciesOptionsMap(settings.currencies)}
                onChange={(currency) => setCurrency(currency)}
              />
            </Col>
            <Col md={4} className="mb-2 mb-md-0">
              <SelectDropdown
                label={t("all_transactions")}
                value={direction}
                options={transactionDirectionsOptions()}
                onChange={(direction) => setDirection(direction)}
              />
            </Col>
            <Col md={4} className="mb-2 mb-md-0">
              <SelectDropdown
                value={sorting}
                options={transactionSortingOptions()}
                onChange={(sort) => setSorting(sort as string)}
              />
            </Col>
          </Row>

          {!!transactions.length ? (
            <TransactionsList
              transactions={transactions}
              onSelect={(transaction) => setTransactionModal(transaction)}
            />
          ) : (
            <div className="text-center my-4">{t("transactions_empty")}</div>
          )}
        </section>

        <TransactionModal
          open={!!transactionModal}
          onClose={() => setTransactionModal(undefined)}
          transaction={transactionModal}
        />
      </Container>
    </>
  );
}

export default Transactions;
