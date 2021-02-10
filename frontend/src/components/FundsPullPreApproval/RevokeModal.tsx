import React, { useEffect, useState } from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import BackendClient from "../../services/backendClient";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../Messages/ErrorMessage";
import SuccessMessage from "../Messages/SuccessMessage";
import { useTranslation } from "react-i18next";

interface RevokeModalProps {
  approval: Approval;
  open: boolean;
  onClose: () => void;
}

function RevokeModal({ approval, open, onClose }: RevokeModalProps) {
  const [submitStatus, setSubmitStatus] = useState<"edit" | "fail" | "success">("edit");
  const [errorMessage, setErrorMessage] = useState<string>();
  const { t } = useTranslation("funds_pull_pre_approval");

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
      await backendClient.updateApprovalStatus(approval.funds_pull_pre_approval_id, "closed");

      setSubmitStatus("success");
      await backendClient.refreshUser();
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage(t("modals.internal_error"));
        console.error(t("modals.unexpected_error"), e);
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
            <SuccessMessage message={t("modals.success_message")} />{" "}
            <Button onClick={onModalClose} color="black" outline className="mt-2">
              {t("done")}
            </Button>
          </>
        )}

        {submitStatus !== "success" && (
          <>
            <h3>{t("revoke_title")}</h3>
            <div className="text-black pb-5">
              {t("modals.revoke_question")} {approval?.biller_name}?
            </div>
            <span>
              <div className="float-right">
                <Button onClick={onModalClose} color="black" outline className="mr-1">
                  {t("modals.cancel")}
                </Button>
                <Button onClick={updateApproval} color="black">
                  {t("revoke")}
                </Button>
              </div>
            </span>{" "}
          </>
        )}
      </ModalBody>
    </Modal>
  );
}

export default RevokeModal;
