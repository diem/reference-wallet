// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Approval } from "../../interfaces/approval";
import ApproveModal from "./ApproveModal";
import RejectModal from "./RejectModal";
import FundsPullPreApproval from "./FundsPullPreApproval";
import RevokeModal from "./RevokeModal";

interface ApprovalsListProps {
  approvals: Approval[];
  displayApproveRejectButtons: boolean;
  displayRevokeButton: boolean;
}

function FundsPullPreApprovalsList({
  approvals,
  displayApproveRejectButtons,
  displayRevokeButton,
}: ApprovalsListProps) {
  const [approveModalOpen, setApproveModalOpen] = useState<boolean>(false);
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [revokeModalOpen, setRevokeModalOpen] = useState<boolean>(false);
  const [approvalInModal, setApprovalInModal] = useState<Approval>();

  return (
    <>
      {approvals.map((approval) => {
        return (
          <FundsPullPreApproval
            key={approval.funds_pull_pre_approval_id}
            approval={approval}
            onApproveClick={() => setApproveModalOpen(true)}
            onRejectClick={() => setRejectModalOpen(true)}
            onRevokeClick={() => setRevokeModalOpen(true)}
            onAnyClickSetApproval={() => setApprovalInModal(approval)}
            displayApproveRejectButtons={displayApproveRejectButtons}
            displayRevokeButton={displayRevokeButton}
          />
        );
      })}

      <ApproveModal
        approval={approvalInModal}
        open={approveModalOpen}
        onClose={() => setApproveModalOpen(false)}
      />
      <RejectModal
        approval={approvalInModal}
        open={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
      />
      <RevokeModal
        approval={approvalInModal}
        open={revokeModalOpen}
        onClose={() => setRevokeModalOpen(false)}
      />
    </>
  );
}

export default FundsPullPreApprovalsList;
