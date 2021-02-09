import React, { useEffect, useState } from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import BackendClient from "../../services/backendClient";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../Messages/ErrorMessage";
import SuccessMessage from "../Messages/SuccessMessage";

interface ApproveModalProps {
  approval: Approval;
  open: boolean;
  onClose: () => void;
}

function ApproveModal({ approval, open, onClose }: ApproveModalProps) {
  const [submitStatus, setSubmitStatus] = useState<"edit" | "fail" | "success">("edit");
  const [errorMessage, setErrorMessage] = useState<string>();

  useEffect(() => {
    async function refreshUser() {
      try {
        await new BackendClient().refreshUser();
      } catch (e) {
        console.error(e);
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();
  }, []);

  const updateApproval = async () => {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("edit");

      const backendClient = new BackendClient();
      await backendClient.updateApprovalStatus(approval.funds_pull_pre_approval_id, "valid");

      setSubmitStatus("success");
      await backendClient.refreshUser();
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  };

  function onModalClose() {
    setSubmitStatus("edit");
    setErrorMessage(undefined);
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onModalClose} />
        {errorMessage && <ErrorMessage message={errorMessage} />}
        {submitStatus === "success" && (
          <>
            <SuccessMessage message={"Approval status successfully updated"} />
            <Button onClick={onModalClose} color="black" outline className="mt-2">
              Done
            </Button>
          </>
        )}

        {submitStatus !== "success" && (
          <>
            <h3>Approve Request</h3>
            <div className="text-black pb-5">
              Are you sure you want to approve the request from {approval?.biller_name}?
            </div>
            <span>
              <div className="float-right">
                <Button onClick={onModalClose} color="black" outline className="mr-1">
                  Cancel
                </Button>
                <Button onClick={updateApproval} color="black">
                  Approve
                </Button>
              </div>
            </span>
          </>
        )}
      </ModalBody>
    </Modal>
  );
}

export default ApproveModal;
