// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { settingsContext } from "../contexts/app";
import { Currency } from "../interfaces/currencies";
import {
  fiatToDiemHumanFriendly,
  diemAmountToFloat,
  diemAmountToHumanFriendly,
} from "../utils/amount-precision";
import { CurrencyBalance } from "../interfaces/account";

interface BalancesListProps {
  balances: CurrencyBalance[];
  onSelect: (currency: Currency) => void;
}

function BalancesList({ balances, onSelect }: BalancesListProps) {
  const [settings] = useContext(settingsContext)!;

  const setActiveCurrency = (activeCurrency: Currency) => () => {
    onSelect(activeCurrency);
  };

  if (!settings.account) {
    return null;
  }

  return (
    <ul className="list-group">
      {balances.map((currencyBalance) => {
        const currency = settings.currencies[currencyBalance.currency];
        const fiatCurrency = settings.fiatCurrencies[settings.defaultFiatCurrencyCode!];
        const exchangeRate = currency.rates[settings.defaultFiatCurrencyCode!];

        const price = diemAmountToFloat(currencyBalance.balance) * exchangeRate;

        return (
          <li
            className="list-group-item list-group-item-action d-flex align-items-center cursor-pointer"
            key={currencyBalance.currency}
            onClick={setActiveCurrency(currencyBalance.currency)}
          >
            <div className="mr-4">
              <strong className="ml-2 text-black">{currency.name}</strong>
            </div>
            <div className="ml-auto text-right">
              <div className="text-black">
                {diemAmountToHumanFriendly(currencyBalance.balance, true)} {currency.sign}
              </div>
              <div className="small">
                {fiatCurrency.sign}
                {fiatToDiemHumanFriendly(price, true)} {fiatCurrency.symbol}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default BalancesList;
