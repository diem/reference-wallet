// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useContext, useEffect, useState } from "react";
import { Button, Form, FormGroup, FormText, Input, Modal, ModalBody } from "reactstrap";
import { v4 as uuid4 } from "uuid";
import CloseButton from "../CloseButton";
import SelectDropdown from "../select";
import { NewPaymentMethod } from "../../interfaces/user";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";

const BANKS = ["My Bank LTD", "My Other Bank"];

interface BankAccount {
  bank: keyof typeof BANKS;
  name: string;
  accountNumber: number;
}

interface CreditCardFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (paymentMethod: NewPaymentMethod) => void;
}

function BankAccountForm({ open, onClose, onSubmit }: CreditCardFormProps) {
  const { t } = useTranslation("settings");
  const [settings] = useContext(settingsContext)!;

  const [bankAccount, setBankAccount] = useState<BankAccount>({
    bank: 0,
    name: "Sherlock Holmes",
    accountNumber: 123456789,
  });

  useEffect(() => {
    if (!settings.user) {
      return;
    }
    setBankAccount({
      ...bankAccount,
      name: `${settings.user!.first_name} ${settings.user!.last_name}`,
    });
  }, [settings]);

  function onFormSubmit(e: FormEvent) {
    e.preventDefault();

    const bank = BANKS[bankAccount.bank];
    const last4digits = bankAccount.accountNumber.toString().slice(-4);

    onSubmit({
      name: `${bankAccount.name} ${bank} (**** ${last4digits})`,
      provider: "BankAccount",
      token: uuid4(),
    });
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <h3>{t("payment_methods.bank_accounts.form.title")}</h3>

        <Form onSubmit={onFormSubmit}>
          <FormGroup>
            <FormText>{t("payment_methods.bank_accounts.form.account_number")}</FormText>
            <Input
              type="number"
              required
              value={bankAccount.accountNumber}
              pattern="[\d| ]{16,22}"
              readOnly
            />
          </FormGroup>

          <FormGroup>
            <FormText>{t("payment_methods.bank_accounts.form.bank")}</FormText>
            <SelectDropdown label="Bank" options={BANKS} value={bankAccount.bank} />
          </FormGroup>

          <FormGroup>
            <FormText>{t("payment_methods.bank_accounts.form.name")}</FormText>
            <Input type="text" required readOnly value={bankAccount.name} />
          </FormGroup>

          <Button color="black" type="submit" block>
            {t("payment_methods.bank_accounts.form.submit")}
          </Button>
        </Form>
      </ModalBody>
    </Modal>
  );
}

export default BankAccountForm;
