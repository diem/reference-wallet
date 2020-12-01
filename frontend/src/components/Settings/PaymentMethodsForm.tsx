// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { ListGroup, ListGroupItem } from "reactstrap";
import { useTranslation } from "react-i18next";
import CreditCardForm from "./CreditCardForm";
import BankAccountForm from "./BackAccountForm";
import { NewPaymentMethod, PaymentMethod, PaymentMethodProviders } from "../../interfaces/user";

type GroupedPaymentMethods = { [key in PaymentMethodProviders]?: PaymentMethod[] };

interface PaymentMethodsFormProps {
  paymentMethods: PaymentMethod[];
  onAdd: (paymentMethod: NewPaymentMethod) => void;
}

function PaymentMethodsForm({ paymentMethods, onAdd }: PaymentMethodsFormProps) {
  const { t } = useTranslation("settings");

  const [creditCardModalOpen, setCreditCardModalOpen] = useState(false);
  const [bankModalOpen, setBankModalOpen] = useState(false);

  async function addPaymentMethod(paymentMethod: NewPaymentMethod) {
    onAdd(paymentMethod);
    setBankModalOpen(false);
    setCreditCardModalOpen(false);
  }

  const { CreditCard, BankAccount }: GroupedPaymentMethods = paymentMethods.reduce(
    (groups, item) => ({
      ...groups,
      [item.provider]: [...(groups[item.provider] || []), item],
    }),
    {}
  );

  return (
    <>
      <h2 className="h5 font-weight-normal text-body mt-4">{t("payment_methods.title")}</h2>

      <h6>{t("payment_methods.credit_cards.title")}</h6>
      <ListGroup className="mb-4">
        {CreditCard?.map((paymentMethod, key) => (
          <ListGroupItem key={key}>{paymentMethod.name}</ListGroupItem>
        ))}
        {!CreditCard && (
          <ListGroupItem>{t("payment_methods.credit_cards.not_found")}</ListGroupItem>
        )}
        <ListGroupItem tag="button" onClick={() => setCreditCardModalOpen(true)}>
          {t("payment_methods.credit_cards.add")}
        </ListGroupItem>
      </ListGroup>

      <h6>{t("payment_methods.bank_accounts.title")}</h6>
      <ListGroup className="mb-4">
        {BankAccount?.map((paymentMethod, key) => (
          <ListGroupItem key={key}>{paymentMethod.name}</ListGroupItem>
        ))}
        {!BankAccount && (
          <ListGroupItem>{t("payment_methods.bank_accounts.not_found")}</ListGroupItem>
        )}
        <ListGroupItem tag="button" onClick={() => setBankModalOpen(true)}>
          {t("payment_methods.bank_accounts.add")}
        </ListGroupItem>
      </ListGroup>

      <CreditCardForm
        open={creditCardModalOpen}
        onClose={() => setCreditCardModalOpen(false)}
        onSubmit={addPaymentMethod}
      />
      <BankAccountForm
        open={bankModalOpen}
        onClose={() => setBankModalOpen(false)}
        onSubmit={addPaymentMethod}
      />
    </>
  );
}

export default PaymentMethodsForm;
