//RejectModal
import React from "react";
import { Modal, ModalBody } from "reactstrap";
import CloseButton from "./CloseButton";

interface RejectModalProps {
  open: boolean;
  onClose: () => void;
}

function RejectModal({ open, onClose }: RejectModalProps) {
  function onModalClose() {
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody>
        <CloseButton onClick={onModalClose} />
        <p>Bond Reject</p>
      </ModalBody>
    </Modal>
  );
}

export default RejectModal;
