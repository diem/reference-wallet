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
  disableApproveRejectButtons?: boolean;
  disableRevokeButton?: boolean;
}

function FundsPullPreApprovalsList({
  approvals,
  disableApproveRejectButtons,
  disableRevokeButton,
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
            onApproveClick={() => {
              setApproveModalOpen(true);
              setApprovalInModal(approval);
            }}
            onRejectClick={() => {
              setRejectModalOpen(true);
              setApprovalInModal(approval);
            }}
            onRevokeClick={() => {
              setRevokeModalOpen(true);
              setApprovalInModal(approval);
            }}
            disableApproveRejectButtons={disableApproveRejectButtons}
            disableRevokeButton={disableRevokeButton}
          />
        );
      })}

      {approvalInModal && (
        <>
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
      )}
    </>
  );
}

export default FundsPullPreApprovalsList;
