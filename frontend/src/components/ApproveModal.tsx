import React from "react";
import { Modal, ModalBody } from "reactstrap";
import CloseButton from "./CloseButton";

interface ApproveModalProps {
  open: boolean;
  onClose: () => void;
}

function ApproveModal({ open, onClose }: ApproveModalProps) {
  function onModalClose() {
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody>
        <CloseButton onClick={onModalClose} />
        <p>Bond Approve</p>
      </ModalBody>
    </Modal>
  );
}

export default ApproveModal;
