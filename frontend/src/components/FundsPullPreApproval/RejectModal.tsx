//RejectModal
import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import ApprovalDetails from "./ApprovalDetails";

interface RejectModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function RejectModal({ approval, open, onClose }: RejectModalProps) {
  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <>
          <h3>Reject Request</h3>
          <ApprovalDetails approval={approval} />
          <span>
            <Button outline onClick={onClose}>
              Cancel
            </Button>
            <Button outline>Reject</Button>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default RejectModal;
