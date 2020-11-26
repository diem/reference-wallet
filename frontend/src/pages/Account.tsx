// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Container } from "reactstrap";
import { match as RouterMatch } from "react-router";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import BackendClient from "../services/backendClient";
import { Currency } from "../interfaces/currencies";
import { Transaction } from "../interfaces/transaction";
import TransactionsList from "../components/TransactionsList";
import Balance from "../components/Balance";
import Actions from "../components/Actions";
import SendModal from "../components/Send/SendModal";
import ReceiveModal from "../components/ReceiveModal";
import TransferModal from "../components/TransferModal";
import TransactionModal from "../components/TransactionModal";
import WalletLoader from "../components/WalletLoader";
import Breadcrumbs from "../components/Breadcrumbs";
import TestnetWarning from "../components/TestnetWarning";

const REFRESH_TRANSACTIONS_INTERVAL = 3000;

function Account({ match }: { match: RouterMatch<{ currency: Currency }> }) {
  const { t } = useTranslation("layout");
  const [settings] = useContext(settingsContext)!;
  const user = settings.user;

  const [transactions, setTransactions] = useState<Transaction[]>([]);

  let selectedCurrency: Currency | undefined = match.params.currency;

  const fetchTransactions = async () => {
    try {
      if (selectedCurrency) {
        setTransactions(await new BackendClient().getTransactions(selectedCurrency));
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
      selectedCurrency = undefined;
    };
  }, []);

  const [transferModalOpen, setTransferModalOpen] = useState<boolean>(false);
  const [sendModalOpen, setSendModalOpen] = useState<boolean>(false);
  const [receiveModalOpen, setReceiveModalOpen] = useState<boolean>(false);
  const [transactionModal, setTransactionModal] = useState<Transaction | undefined>();

  return (
    <>
      <TestnetWarning />

      <Breadcrumbs pageName={settings.currencies[selectedCurrency].name + " Wallet"} />
      <Container className="py-5">
        {user && (
          <>
            <h1 className="h5 font-weight-normal text-body text-center mb-4">
              {settings.currencies[selectedCurrency].name} Wallet
            </h1>

            <section className="my-5 text-center">
              <Balance currency={selectedCurrency} />
            </section>

            <section className="my-5 text-center">
              <Actions
                onSendClick={() => setSendModalOpen(true)}
                onRequestClick={() => setReceiveModalOpen(true)}
                onTransferClick={() => setTransferModalOpen(true)}
              />
            </section>

            <section className="my-5">
              {transactions.length ? (
                <>
                  <h2 className="h5 font-weight-normal text-body">{t("transactions")}</h2>
                  <TransactionsList
                    transactions={transactions}
                    onSelect={(transaction) => setTransactionModal(transaction)}
                  />
                </>
              ) : (
                <div className="text-center">{t("transactions_empty")}</div>
              )}
            </section>

            <SendModal
              open={sendModalOpen}
              initialCurrency={selectedCurrency}
              onClose={() => setSendModalOpen(false)}
            />
            <ReceiveModal
              open={receiveModalOpen}
              currency={selectedCurrency}
              onClose={() => setReceiveModalOpen(false)}
            />
            <TransferModal
              open={transferModalOpen}
              currency={selectedCurrency}
              onClose={() => setTransferModalOpen(false)}
            />
            <TransactionModal
              open={!!transactionModal}
              onClose={() => setTransactionModal(undefined)}
              transaction={transactionModal}
            />
          </>
        )}
        {!user && <WalletLoader />}
      </Container>
    </>
  );
}

export default Account;
