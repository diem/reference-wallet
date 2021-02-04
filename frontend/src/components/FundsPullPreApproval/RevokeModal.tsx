import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import BackendClient from "../../services/backendClient";

interface RevokeModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function RevokeModal({ approval, open, onClose }: RevokeModalProps) {
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
          <h3>Revoke Request</h3>
          <div className="text-black pb-5">
            Are you sure you want to revoke the request from {approval?.biller_name}?
          </div>
          <span>
            <div className="float-right">
              <Button onClick={onClose} color="black" outline className="mr-1">
                Cancel
              </Button>
              <Button onClick={updateApproval} color="black">
                Revoke
              </Button>
            </div>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default RevokeModal;
