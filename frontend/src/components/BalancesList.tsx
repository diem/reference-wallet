// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { settingsContext } from "../contexts/app";
import { LibraCurrency } from "../interfaces/currencies";
import { fiatToHumanFriendly, libraToFloat, libraToHumanFriendly } from "../utils/amount-precision";
import { LibraCurrencyBalance } from "../interfaces/account";

interface BalancesListProps {
  balances: LibraCurrencyBalance[];
  onSelect: (currency: LibraCurrency) => void;
}

function BalancesList({ balances, onSelect }: BalancesListProps) {
  const [settings] = useContext(settingsContext)!;

  const setActiveCurrency = (activeCurrency: LibraCurrency) => () => {
    onSelect(activeCurrency);
  };

  if (!settings.account) {
    return null;
  }

  return (
    <ul className="list-group">
      {balances.map((currencyBalance) => {
        const libraCurrency = settings.currencies[currencyBalance.currency];
        const fiatCurrency = settings.fiatCurrencies[settings.defaultFiatCurrencyCode!];
        const exchangeRate = libraCurrency.rates[settings.defaultFiatCurrencyCode!];

        const price = libraToFloat(currencyBalance.balance) * exchangeRate;

        return (
          <li
            className="list-group-item list-group-item-action d-flex align-items-center cursor-pointer"
            key={currencyBalance.currency}
            onClick={setActiveCurrency(currencyBalance.currency)}
          >
            <div className="mr-4">
              <strong className="ml-2 text-black">{libraCurrency.name}</strong>
            </div>
            <div className="ml-auto text-right">
              <div className="text-black">
                {libraToHumanFriendly(currencyBalance.balance, true)} {libraCurrency.sign}
              </div>
              <div className="small">
                {fiatCurrency.sign}
                {fiatToHumanFriendly(price, true)} {fiatCurrency.symbol}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default BalancesList;
