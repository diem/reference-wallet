//RejectModal
import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import ApprovalDetails from "./ApprovalDetails";
import BackendClient from "../../services/backendClient";

interface RejectModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function RejectModal({ approval, open, onClose }: RejectModalProps) {
  const updateApproval = async () => {
    try {
      await new BackendClient().updateApprovalStatus(
        approval!.funds_pull_pre_approval_id,
        "rejected"
      );
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
          <h3>Reject Request</h3>
          <ApprovalDetails approval={approval} />
          <span className="mt-3">Are you sure you want to reject this request?</span>
          <span>
            <Button outline onClick={onClose}>
              Cancel
            </Button>
            <Button outline onClick={updateApproval}>
              Reject
            </Button>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default RejectModal;
