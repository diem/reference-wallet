// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { settingsContext } from "../contexts/app";
import { diemAmountToHumanFriendly } from "../utils/amount-precision";
import { Debt } from "../interfaces/settlement";

export interface SettlementDetailsProps {
  debt: Debt[];
}

export default function SettlementDetails({ debt }: SettlementDetailsProps) {
  const [settings] = useContext(settingsContext)!;

  return (
    <ul className="list-group">
      {debt.map(({ currency, amount }) => {
        const symbol = settings.fiatCurrencies[currency].sign;
        return (
          <li
            className="list-group-item list-group-item-action d-flex align-items-center cursor-pointer"
            key={currency}
          >
            <div className="mr-4">
              <strong className="ml-2 text-black">{currency}</strong>
            </div>
            <div className="ml-auto text-right">
              <div className="text-black">
                {diemAmountToHumanFriendly(amount, true)} {symbol}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
