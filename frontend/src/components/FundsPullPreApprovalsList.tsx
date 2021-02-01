// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Approval } from "../interfaces/approval";
import { classNames } from "../utils/class-names";
import { settingsContext } from "../contexts/app";
import { diemAmountToHumanFriendly } from "../utils/amount-precision";

interface ApprovalsListProps {
  approvals: Approval[];
}

function FundsPullPreApprovalsList({ approvals }: ApprovalsListProps) {
  const [settings] = useContext(settingsContext)!;

  const itemStyles = {
    "list-group-item": true,
    // "list-group-item-action": !!onSelect,
    // "cursor-pointer": !!onSelect,
  };

  function approveRequest() {}

  return (
    <>
      <ul>
        {approvals.map((approval) => {
          return (
            <li
              className={classNames(itemStyles)}
              key={approval.funds_pull_pre_approval_id}
              // onClick={() => onSelect && onSelect(transaction)}
            >
              <span>
                <div className="text-black">
                  <span>
                    Received from <b>{approval.biller_name}</b>
                  </span>{" "}
                  (<span>{new Date(approval.created_timestamp).toLocaleString()})</span>
                </div>
                <div className="text-black">
                  <strong>{"Limits:"}</strong>
                </div>
                <div className="text-black">
                  {!approval.scope.max_cumulative_amount &&
                    !approval.scope.max_transaction_amount &&
                    "No Limits"}
                </div>
                <div className="text-black">
                  {approval.scope.max_transaction_amount &&
                    "Single payment limit: Up to " +
                      diemAmountToHumanFriendly(
                        approval.scope.max_transaction_amount.amount,
                        true
                      ) +
                      settings.currencies[approval.scope.max_transaction_amount.currency].sign}{" "}
                </div>
                <div className="text-black">
                  {approval.scope.max_cumulative_amount &&
                    "Total payments limit: Up to " +
                      diemAmountToHumanFriendly(
                        approval.scope.max_cumulative_amount.max_amount.amount,
                        true
                      ) +
                      " " +
                      settings.currencies[approval.scope.max_cumulative_amount.max_amount.currency]
                        .sign +
                      " every " +
                      approval.scope.max_cumulative_amount.value +
                      " " +
                      approval.scope.max_cumulative_amount.unit +
                      (approval.scope.max_cumulative_amount.value > 1 ? "s" : "")}
                </div>
                <div className="small ml-auto ">
                  {"Last payment allowed on "}
                  {new Date(approval.scope.expiration_timestamp).toLocaleString()}
                </div>
              </span>
              <span className="float-right">
                <button type="button" className="btn btn-success btn-sm">
                  Approve
                </button>
                <button type="button" className="btn btn-danger btn-sm">
                  Reject
                </button>
              </span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

export default FundsPullPreApprovalsList;
