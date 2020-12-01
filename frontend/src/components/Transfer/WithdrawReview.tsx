// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Badge, Button } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";
import {
  fiatToDiemHumanFriendly,
  fiatToHumanFriendlyRate,
  diemAmountToHumanFriendly,
} from "../../utils/amount-precision";
import { Quote } from "../../interfaces/cico";
import { paymentMethodsLabels } from "../../interfaces/user";

interface WithdrawReviewProps {
  quote: Quote;
  fundingSourceId: number;
  submitting: boolean;
  submitted: boolean;
  onBack: () => void;
  onConfirm: () => void;
  onComplete: () => void;
}

function WithdrawReview({
  quote,
  fundingSourceId,
  submitting,
  submitted,
  onBack,
  onConfirm,
  onComplete,
}: WithdrawReviewProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;

  const fundingSource = settings.paymentMethods!.find(
    (paymentMethod) => paymentMethod.id == fundingSourceId
  )!;

  const [currencyCode, fiatCode] = quote.rfq.currency_pair.split("_");

  const currency = settings.currencies[currencyCode];
  const fiatCurrency = settings.fiatCurrencies[fiatCode];

  const exchangeRate = currency.rates[fiatCurrency.symbol];

  return (
    <>
      <h3>{t("withdraw.review.title")}</h3>
      <p>{t("withdraw.review.description")}</p>

      <div>
        <small>{t("withdraw.review.funding_source")}</small>
        <p className="text-black">
          {fundingSource.name} <Badge>{paymentMethodsLabels[fundingSource.provider]}</Badge>
        </p>
      </div>

      <div>
        <small>{t("withdraw.review.amount")}</small>
        <p className="text-black">
          {diemAmountToHumanFriendly(quote.rfq.amount, true)} {currency.sign}
        </p>
      </div>

      <div>
        <small>{t("withdraw.review.price")}</small>
        <p className="text-black">
          {fiatCurrency.sign}
          {fiatToDiemHumanFriendly(quote.price, true)} {fiatCurrency.symbol}
        </p>
      </div>

      <div>
        <small>{t("withdraw.review.exchange_rate")}</small>
        <p className="text-black">
          1 {currency.sign} = {fiatToHumanFriendlyRate(exchangeRate)} {fiatCurrency.symbol}
        </p>
      </div>

      {!submitted && (
        <>
          <Button color="black" block onClick={onConfirm} disabled={submitting}>
            {submitting ? <i className="fa fa-spin fa-spinner" /> : t("withdraw.review.confirm")}
          </Button>
          <Button outline color="black" block onClick={onBack} disabled={submitting}>
            {t("withdraw.review.back")}
          </Button>
        </>
      )}
      {submitted && (
        <Button outline color="black" block onClick={onComplete}>
          {t("withdraw.review.done")}
        </Button>
      )}
    </>
  );
}

export default WithdrawReview;
