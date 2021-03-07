import React, { useContext } from "react";
import { Approval } from "../../interfaces/approval";
import { diemAmountToHumanFriendly } from "../../utils/amount-precision";
import { settingsContext } from "../../contexts/app";
import { useTranslation } from "react-i18next";

interface RequestDetailsProps {
  approval: Approval;
}

function ApprovalDetails({ approval }: RequestDetailsProps) {
  const [settings] = useContext(settingsContext)!;
  const { t } = useTranslation("funds_pull_pre_approval");

  const dateToDisplayByApprovalStatus = () => {
    if (approval.status === "pending") {
      return (
        <>
          {t("on")} <span>{new Date(approval.created_at).toLocaleString()}</span>
        </>
      );
    }
    if (approval.status === "rejected") {
      return (
        <div>
          {t("rejected_on")} <span>{new Date(approval.updated_at).toLocaleString()}</span>
        </div>
      );
    }
    if (approval.status === "closed") {
      return (
        <>
          <div>
            {t("approved_on")} <span>{new Date(approval.approved_at).toLocaleString()}</span>
          </div>
          <div>
            {t("revoked_on")} <span>{new Date(approval.updated_at).toLocaleString()}</span>
          </div>
        </>
      );
    }
    if (approval.status === "valid") {
      const expiration_timestamp = new Date(approval.scope.expiration_timestamp * 1000);
      const now = new Date();
      if (expiration_timestamp < now) {
        return (
          <>
            <div>
              {t("approved_on")} <span>{new Date(approval.approved_at).toLocaleString()}</span>
            </div>
            <div>
              {t("expired_on")} <span>{expiration_timestamp.toLocaleString()}</span>
            </div>
          </>
        );
      }

      return (
        <div>
          {t("approved_on")} <span>{new Date(approval.updated_at).toLocaleString()}</span>
        </div>
      );
    }
  };

  return (
    <span>
      <div className="text-black">
        <span>
          {t("received_from")} <b>{approval.biller_name}</b>
        </span>{" "}
        {dateToDisplayByApprovalStatus()}
      </div>
      {approval?.description && <div>{approval.description}</div>}
      <div className="pt-1">
        <div className="text-black ">
          {!approval.scope.max_cumulative_amount &&
            !approval.scope.max_transaction_amount &&
            t("no_limits")}
        </div>
        <div className="text-black ">
          {approval.scope.max_transaction_amount && (
            <>
              {t("single_payment")}{" "}
              {diemAmountToHumanFriendly(approval.scope.max_transaction_amount.amount, true)}{" "}
              {settings.currencies[approval.scope.max_transaction_amount.currency].sign}{" "}
            </>
          )}
        </div>
        <div className="text-black ">
          {approval.scope.max_cumulative_amount && (
            <>
              {t("total_payments")}{" "}
              {diemAmountToHumanFriendly(
                approval.scope.max_cumulative_amount.max_amount.amount,
                true
              )}{" "}
              {settings.currencies[approval.scope.max_cumulative_amount.max_amount.currency].sign}{" "}
              {t("every")} {approval.scope.max_cumulative_amount.value}{" "}
              {approval.scope.max_cumulative_amount.unit}
              {approval.scope.max_cumulative_amount.value > 1 ? t("plural_suffix") : ""}
            </>
          )}
        </div>
        <div>
          {t("last_payment")}{" "}
          {new Date(approval.scope.expiration_timestamp * 1000).toLocaleString()}
        </div>
      </div>
    </span>
  );
}

export default ApprovalDetails;
