import React, { useContext } from "react";
import { Approval } from "../../interfaces/approval";
import { diemAmountToHumanFriendly } from "../../utils/amount-precision";
import { settingsContext } from "../../contexts/app";

interface RequestDetailsProps {
  approval: Approval | undefined;
}

function ApprovalDetails({ approval }: RequestDetailsProps) {
  const [settings] = useContext(settingsContext)!;

  function dateToDisplay(text: string, timestamp: string) {
    return (
      <>
        {text} <span>{new Date(timestamp).toLocaleString()}</span>
      </>
    );
  }

  const dateToDisplayByApprovalStatus = () => {
    if (approval!.status === "pending") {
      return dateToDisplay("on", approval!.created_at);
    }
    if (approval!.status === "rejected") {
      return dateToDisplay("rejected on", approval!.updated_at);
    }
    if (approval!.status === "closed") {
      return dateToDisplay("revoked on", approval!.updated_at);
    }
    if (approval!.status === "valid") {
      const now = new Date().toISOString();
      if (Date.parse(approval!.scope.expiration_timestamp) < Date.parse(now)) {
        return dateToDisplay("expired at", approval!.scope.expiration_timestamp);
      }

      return dateToDisplay("approved on", approval!.updated_at);
    }
  };

  return (
    <span>
      <div className="text-black">
        <span>
          Received from <b>{approval!.biller_name}</b>
        </span>{" "}
        {dateToDisplayByApprovalStatus()}
      </div>
      {approval?.description && <div>{approval.description}</div>}
      <div className="pt-1">
        <div className="text-black ">
          {!approval!.scope.max_cumulative_amount &&
            !approval!.scope.max_transaction_amount &&
            "No Limits"}
        </div>
        <div className="text-black ">
          {approval!.scope.max_transaction_amount &&
            "Single payment limit: Up to " +
              diemAmountToHumanFriendly(approval!.scope.max_transaction_amount.amount, true) +
              settings.currencies[approval!.scope.max_transaction_amount.currency].sign}{" "}
        </div>
        <div className="text-black ">
          {approval!.scope.max_cumulative_amount &&
            "Total payments limit: Up to " +
              diemAmountToHumanFriendly(
                approval!.scope.max_cumulative_amount.max_amount.amount,
                true
              ) +
              " " +
              settings.currencies[approval!.scope.max_cumulative_amount.max_amount.currency].sign +
              " every " +
              approval!.scope.max_cumulative_amount.value +
              " " +
              approval!.scope.max_cumulative_amount.unit +
              (approval!.scope.max_cumulative_amount.value > 1 ? "s" : "")}
        </div>
        <div>
          {"Last payment allowed on "}
          {new Date(approval!.scope.expiration_timestamp).toLocaleString()}
        </div>
      </div>
    </span>
  );
}

export default ApprovalDetails;
