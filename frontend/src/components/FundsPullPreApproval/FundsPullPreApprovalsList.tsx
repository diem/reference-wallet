// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Approval } from "../../interfaces/approval";
import ApproveModal from "./ApproveModal";
import RejectModal from "./RejectModal";
import FundsPullPreApproval from "./FundsPullPreApproval";
import CloseModal from "./CloseModal";

interface ApprovalsListProps {
  approvals: Approval[];
  displayApproveRejectButtons: boolean;
  displayCloseButton: boolean;
}

function FundsPullPreApprovalsList({
  approvals,
  displayApproveRejectButtons,
  displayCloseButton,
}: ApprovalsListProps) {
  const [approveModalOpen, setApproveModalOpen] = useState<boolean>(false);
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [closeModalOpen, setCloseModalOpen] = useState<boolean>(false);
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
            onCloseClick={() => setCloseModalOpen(true)}
            onAnyClickSetApproval={() => setApprovalInModal(approval)}
            displayApproveRejectButtons={displayApproveRejectButtons}
            displayCloseButton={displayCloseButton}
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
      <CloseModal
        approval={approvalInModal}
        open={closeModalOpen}
        onClose={() => setCloseModalOpen(false)}
      />
    </>
  );
}

export default FundsPullPreApprovalsList;
