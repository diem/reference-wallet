import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import ApprovalDetails from "./ApprovalDetails";
import BackendClient from "../../services/backendClient";

interface ApproveModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function ApproveModal({ approval, open, onClose }: ApproveModalProps) {
  const updateApproval = async () => {
    try {
      await new BackendClient().updateApprovalStatus(approval!.funds_pull_pre_approval_id, "valid");
    } catch (e) {
      console.error(e);
    }

    onClose();
  };

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <>
          <h3>Approve Request</h3>
          <div className="text-black">
            Please confirm your approval for the fund pre-approval request from{" "}
            {approval?.biller_name}.
          </div>
          <span className="mt-3">Are you sure you want to approve this request?</span>
          <span>
            <Button outline onClick={onClose}>
              Cancel
            </Button>
            <Button outline onClick={updateApproval}>
              Approve
            </Button>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default ApproveModal;
