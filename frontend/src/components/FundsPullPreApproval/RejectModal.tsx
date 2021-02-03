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
          <div className="text-black  pb-5">
            Are you sure you want to reject the request from {approval?.biller_name}?
          </div>
          <span>
            <div className="float-right">
              <Button color="black" outline onClick={onClose} className="mr-1">
                Cancel
              </Button>
              <Button color="black" onClick={updateApproval}>
                Reject
              </Button>
            </div>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default RejectModal;
