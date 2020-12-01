// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../contexts/app";
import { LibraCurrency } from "../interfaces/currencies";
import { fiatToHumanFriendly, libraToFloat, libraToHumanFriendly } from "../utils/amount-precision";

interface BalanceProps {
  currency: LibraCurrency;
}

function Balance({ currency }: BalanceProps) {
  const { t } = useTranslation("layout");
  const [settings] = useContext(settingsContext)!;

  if (!settings.account) {
    return null;
  }

  const currencyBalance = settings.account.balances.find(
    (currencyBalance) => currencyBalance.currency === currency
  );

  if (!currencyBalance) {
    return null;
  }

  const defaultFiatCurrencyCode = settings.defaultFiatCurrencyCode!;
  const fiatCurrency = settings.fiatCurrencies[defaultFiatCurrencyCode];
  const libraCurrency = settings.currencies[currency];

  const exchangeRate = libraCurrency.rates[defaultFiatCurrencyCode];
  const price = libraToFloat(currencyBalance.balance) * exchangeRate;

  return (
    <>
      <div className="h3 m-0">
        {libraToHumanFriendly(currencyBalance.balance, true)} {libraCurrency.sign}
      </div>
      {t("price")} {fiatCurrency.sign}
      {fiatToHumanFriendly(price, true)} {fiatCurrency.symbol}
    </>
  );
}

export default Balance;
