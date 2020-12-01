// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useContext, useEffect, useState } from "react";
import { Button, Col, Form, FormGroup, FormText, Input, Modal, ModalBody, Row } from "reactstrap";
import ReactCreditCard, { ReactCreditCardProps } from "react-credit-cards";
import { v4 as uuid4 } from "uuid";
import CloseButton from "../CloseButton";
import { NewPaymentMethod } from "../../interfaces/user";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";

interface CreditCardFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (paymentMethod: NewPaymentMethod) => void;
}

function CreditCardForm({ open, onClose, onSubmit }: CreditCardFormProps) {
  const { t } = useTranslation("settings");
  const [settings] = useContext(settingsContext)!;

  const [creditCard, setCreditCard] = useState<ReactCreditCardProps>({
    number: 4111111111111111,
    name: "Sherlock Holmes",
    expiry: "12/20",
    cvc: 123,
    focused: undefined,
  });

  useEffect(() => {
    if (!settings.user) {
      return;
    }
    setCreditCard({
      ...creditCard,
      name: `${settings.user!.first_name} ${settings.user!.last_name}`,
    });
  }, [settings]);

  function onFormSubmit(e: FormEvent) {
    e.preventDefault();
    const last4digits = creditCard.number.toString().slice(-4);
    onSubmit({
      name: `${creditCard.name} (**** **** **** ${last4digits} ${creditCard.expiry})`,
      provider: "CreditCard",
      token: uuid4(),
    });
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <h3>{t("payment_methods.credit_cards.form.title")}</h3>
        <ReactCreditCard
          issuer="unknown"
          preview={true}
          number={creditCard.number}
          name={creditCard.name}
          expiry={creditCard.expiry}
          cvc={creditCard.cvc}
          focused={creditCard.focused}
        />

        <Form onSubmit={onFormSubmit} className="mt-4">
          <FormGroup>
            <FormText>{t("payment_methods.credit_cards.form.number")}</FormText>
            <Input
              type="number"
              required
              value={creditCard.number}
              pattern="[\d| ]{16,22}"
              readOnly
              onFocus={() => setCreditCard({ ...creditCard, focused: "number" })}
            />
          </FormGroup>

          <FormGroup>
            <FormText>{t("payment_methods.credit_cards.form.name")}</FormText>
            <Input
              type="text"
              required
              value={creditCard.name}
              readOnly
              onFocus={() => setCreditCard({ ...creditCard, focused: "name" })}
            />
          </FormGroup>

          <Row>
            <Col>
              <FormGroup>
                <FormText>{t("payment_methods.credit_cards.form.expiry")}</FormText>
                <Input
                  type="tel"
                  required
                  pattern="\d\d/\d\d"
                  value={creditCard.expiry}
                  readOnly
                  onFocus={() => setCreditCard({ ...creditCard, focused: "expiry" })}
                />
              </FormGroup>
            </Col>

            <Col>
              <FormGroup>
                <FormText>{t("payment_methods.credit_cards.form.cvc")}</FormText>
                <Input
                  type="tel"
                  required
                  pattern="\d{3,4}"
                  value={creditCard.cvc}
                  readOnly
                  onFocus={() => setCreditCard({ ...creditCard, focused: "cvc" })}
                />
              </FormGroup>
            </Col>
          </Row>

          <Button color="black" type="submit" block>
            {t("payment_methods.credit_cards.form.submit")}
          </Button>
        </Form>
      </ModalBody>
    </Modal>
  );
}

export default CreditCardForm;
