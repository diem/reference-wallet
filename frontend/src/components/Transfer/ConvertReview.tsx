// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Button } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";
import { Quote } from "../../interfaces/cico";
import { diemAmountToHumanFriendly } from "../../utils/amount-precision";

interface ConvertReviewProps {
  quote: Quote;
  submitting: boolean;
  submitted: boolean;
  onBack: () => void;
  onConfirm: () => void;
  onComplete: () => void;
}

function ConvertReview({
  quote,
  submitting,
  submitted,
  onBack,
  onConfirm,
  onComplete,
}: ConvertReviewProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;

  const [fromCode, toCode] = quote.rfq.currency_pair.split("_");

  const fromCurrency = settings.currencies[fromCode];
  const toCurrency = settings.currencies[toCode];

  const exchangeRate = fromCurrency.rates[toCode];

  return (
    <>
      <h3>{t("convert.review.title")}</h3>
      <p>{t("convert.review.description")}</p>

      <div>
        <small>{t("convert.review.amount")}</small>
        <p className="text-black">
          {diemAmountToHumanFriendly(quote.rfq.amount, true)} {fromCurrency.sign}
        </p>
      </div>

      <div>
        <small>{t("convert.review.price")}</small>
        <p className="text-black">
          {diemAmountToHumanFriendly(quote.price)} {toCurrency.sign}
        </p>
      </div>

      <div>
        <small>{t("convert.review.exchange_rate")}</small>
        <p className="text-black">
          1 {fromCurrency.sign} = {diemAmountToHumanFriendly(exchangeRate)} {toCurrency.sign}
        </p>
      </div>

      {!submitted && (
        <>
          <Button color="black" block onClick={onConfirm} disabled={submitting}>
            {submitting ? <i className="fa fa-spin fa-spinner" /> : t("convert.review.confirm")}
          </Button>
          <Button outline color="black" block onClick={onBack} disabled={submitting}>
            {t("convert.review.back")}
          </Button>
        </>
      )}
      {submitted && (
        <Button outline color="black" block onClick={onComplete}>
          {t("convert.review.done")}
        </Button>
      )}
    </>
  );
}

export default ConvertReview;
