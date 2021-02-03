import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import BackendClient from "../../services/backendClient";

interface ApproveModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function CloseModal({ approval, open, onClose }: ApproveModalProps) {
  const updateApproval = async () => {
    try {
      await new BackendClient().updateApprovalStatus(
        approval!.funds_pull_pre_approval_id,
        "closed"
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
          <h3>Close Request</h3>
          <div className="text-black pb-5">
            Are you sure you want to close the request from {approval?.biller_name}?
          </div>
          <span>
            <div className="float-right">
              <Button onClick={onClose} color="black" outline className="mr-1">
                Cancel
              </Button>
              <Button onClick={updateApproval} color="black">
                Close
              </Button>
            </div>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default CloseModal;
