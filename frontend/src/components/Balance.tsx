// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { Currency } from "../interfaces/currencies";
import {
  fiatToDiemHumanFriendly,
  diemAmountToFloat,
  diemAmountToHumanFriendly,
} from "../utils/amount-precision";

interface BalanceProps {
  currencyCode: Currency;
}

function Balance({ currencyCode }: BalanceProps) {
  const { t } = useTranslation("layout");
  const [settings] = useContext(settingsContext)!;

  if (!settings.account) {
    return null;
  }

  const currencyBalance = settings.account.balances.find(
    (currencyBalance) => currencyBalance.currency === currencyCode
  );

  if (!currencyBalance) {
    return null;
  }

  const defaultFiatCurrencyCode = settings.defaultFiatCurrencyCode!;
  const fiatCurrency = settings.fiatCurrencies[defaultFiatCurrencyCode];
  const currency = settings.currencies[currencyCode];

  const exchangeRate = currency.rates[defaultFiatCurrencyCode];
  const price = diemAmountToFloat(currencyBalance.balance) * exchangeRate;

  return (
    <>
      <div className="h3 m-0">
        {diemAmountToHumanFriendly(currencyBalance.balance, true)} {currency.sign}
      </div>
      {t("price")} {fiatCurrency.sign}
      {fiatToDiemHumanFriendly(price, true)} {fiatCurrency.symbol}
    </>
  );
}

export default Balance;
