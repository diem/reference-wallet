// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Approval } from "../interfaces/approval";
import ApproveModal from "./ApproveModal";
import RejectModal from "./RejectModal";
import FundsPullPreApproval from "./FundsPullPreApproval";

interface ApprovalsListProps {
  approvals: Approval[];
}

function FundsPullPreApprovalsList({ approvals }: ApprovalsListProps) {
  const [approveModalOpen, setApproveModalOpen] = useState<boolean>(false);
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);

  return (
    <>
      <ul className="list-group my-4">
        {approvals.map((approval) => {
          return (
            <FundsPullPreApproval
              approval={approval}
              onApproveClick={() => setApproveModalOpen(true)}
              onRejectClick={() => setRejectModalOpen(true)}
            />
          );
        })}
      </ul>
      <ApproveModal open={approveModalOpen} onClose={() => setApproveModalOpen(false)} />
      <RejectModal open={rejectModalOpen} onClose={() => setRejectModalOpen(false)} />
    </>
  );
}

export default FundsPullPreApprovalsList;
