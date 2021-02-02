import { Approval } from "../../interfaces/approval";
import React, { useContext } from "react";
import { settingsContext } from "../../contexts/app";
import { classNames } from "../../utils/class-names";
import { diemAmountToHumanFriendly } from "../../utils/amount-precision";
import { Button } from "reactstrap";
import ApprovalDetails from "./ApprovalDetails";

interface ApprovalProps {
  approval: Approval;
  onApproveClick: () => void;
  onRejectClick: () => void;
  onAnyClickSetApproval: () => void;
}

function FundsPullPreApproval({
  approval,
  onApproveClick,
  onRejectClick,
  onAnyClickSetApproval,
}: ApprovalProps) {
  const itemStyles = {
    "list-group-item": true,
  };

  const onAnyClick = (method: () => void) => () => {
    method();
    onAnyClickSetApproval();
  };

  return (
    <li className={classNames(itemStyles)} key={approval.funds_pull_pre_approval_id}>
      <ApprovalDetails approval={approval} />
      <span className="float-right">
        <Button
          className="mr-1"
          size="sm"
          disabled={!onRejectClick}
          onClick={onAnyClick(onRejectClick)}
        >
          Reject
        </Button>
        <Button size="sm" disabled={!onApproveClick} onClick={onAnyClick(onApproveClick)}>
          Approve
        </Button>
      </span>
    </li>
  );
}

export default FundsPullPreApproval;
