// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Approval } from "../interfaces/approval";
import { classNames } from "../utils/class-names";

interface ApprovalsListProps {
  approvals: Approval[];
}

function FundsPullPreApprovalsList({ approvals }: ApprovalsListProps) {
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
              <div className="d-flex">
                <>
                  <span className="text-black mr-4 overflow-auto">
                    <div>
                      Received from <b>{approval.biller_name}</b> (
                      {new Date(approval.created_timestamp).toLocaleString()})
                      {/*// new Date(approval.created_timestamp).toLocaleDateString()*/}
                    </div>

                    <div className="text-black mr-4 overflow-auto inline-block">
                      <strong>{"Limits:"}</strong>{" "}
                    </div>
                  </span>
                  {/*<Button color="black" outline onClick={approveRequest}>*/}
                  {/*  {"Approve"}*/}
                  {/*</Button>*/}
                  {/*<Button color="black" outline>*/}
                  {/*  {"Reject"}*/}
                  {/*</Button>*/}
                </>
              </div>
            </li>
          );
        })}
      </ul>
    </>
  );
}

export default FundsPullPreApprovalsList;
