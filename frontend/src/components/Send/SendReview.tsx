// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Button } from "reactstrap";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";
import { Send } from "./interfaces";
import { fiatToHumanFriendly, fiatToHumanFriendlyRate } from "../../utils/amount-precision";

interface SendReviewProps {
  data: Required<Send>;
  submitting: boolean;
  submitted: boolean;
  onBack: () => void;
  onConfirm: () => void;
  onComplete: () => void;
}

function SendReview({
  data,
  submitting,
  submitted,
  onBack,
  onConfirm,
  onComplete,
}: SendReviewProps) {
  const { t } = useTranslation("send");
  const [settings] = useContext(settingsContext)!;

  const libraCurrency = settings.currencies[data.libraCurrency];
  const fiatCurrency = settings.fiatCurrencies[data.fiatCurrency];

  const exchangeRate = libraCurrency.rates[fiatCurrency.symbol];

  function calcPrice(libraAmount: number) {
    return libraAmount * exchangeRate;
  }

  return (
    <>
      <h3>{t("review.title")}</h3>
      <p>{t("review.description")}</p>

      <div>
        <small>{t("review.amount")}</small>
        <p className="text-black">
          {data.libraAmount} {libraCurrency.sign}
        </p>
      </div>

      <div>
        <small>{t("review.price")}</small>
        <p className="text-black">
          {fiatToHumanFriendly(calcPrice(data.libraAmount), true)} {fiatCurrency.symbol}
        </p>
      </div>

      <div>
        <small>{t("review.exchange_rate")}</small>
        <p className="text-black">
          1 {libraCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)} {fiatCurrency.symbol}
        </p>
      </div>

      <div>
        <small>{t("review.address")}</small>
        <p className="text-black">{data.libraAddress}</p>
      </div>

      {!submitted && (
        <>
          <Button color="black" block onClick={onConfirm} disabled={submitting}>
            {submitting ? <i className="fa fa-spin fa-spinner" /> : t("review.confirm")}
          </Button>
          <Button outline color="black" block onClick={onBack} disabled={submitting}>
            {t("review.back")}
          </Button>
        </>
      )}
      {submitted && (
        <Button outline color="black" block onClick={onComplete}>
          {t("review.done")}
        </Button>
      )}
    </>
  );
}

export default SendReview;
