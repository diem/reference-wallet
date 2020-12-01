// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Button } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";
import { Quote } from "../../interfaces/cico";
import { libraToHumanFriendly } from "../../utils/amount-precision";

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

  const fromLibraCurrency = settings.currencies[fromCode];
  const toLibraCurrency = settings.currencies[toCode];

  const exchangeRate = fromLibraCurrency.rates[toCode];

  return (
    <>
      <h3>{t("convert.review.title")}</h3>
      <p>{t("convert.review.description")}</p>

      <div>
        <small>{t("convert.review.amount")}</small>
        <p className="text-black">
          {libraToHumanFriendly(quote.rfq.amount, true)} {fromLibraCurrency.sign}
        </p>
      </div>

      <div>
        <small>{t("convert.review.price")}</small>
        <p className="text-black">
          {libraToHumanFriendly(quote.price)} {toLibraCurrency.sign}
        </p>
      </div>

      <div>
        <small>{t("convert.review.exchange_rate")}</small>
        <p className="text-black">
          1 {fromLibraCurrency.sign} = {libraToHumanFriendly(exchangeRate)} {toLibraCurrency.sign}
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
