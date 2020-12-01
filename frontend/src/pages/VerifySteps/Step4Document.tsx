// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import Dropzone from "react-dropzone";
import { Button, Card, CardBody, CardFooter, Col, Form, Row } from "reactstrap";
import { countries } from "countries-list";
import { UserInfo } from "../../interfaces/user";

interface Step4DocumentProps {
  info: UserInfo;
  onSubmit: (value: File) => void;
  onBack: () => void;
}

const Step4Document = ({ info, onBack, onSubmit }: Step4DocumentProps) => {
  const { t } = useTranslation("verify");
  const [selectedFile, setSelectedFile] = useState<File | undefined>();

  const onDrop = (acceptedFiles: File[]) => setSelectedFile(acceptedFiles[0]);

  const onFormSubmit = async (e: FormEvent) => {
    e.preventDefault();
    onSubmit(selectedFile!);
  };

  return (
    <>
      <h1 className="h3">{t("step4.title")}</h1>
      <p>{t("step4.description")}</p>

      <Form role="form" onSubmit={onFormSubmit}>
        <Dropzone onDrop={onDrop} multiple={false} accept="image/*">
          {({ getRootProps, getInputProps, isDragActive }) => (
            <Card
              {...getRootProps({ refKey: "innerRef" })}
              className="text-black mb-4 cursor-pointer"
            >
              <CardBody>
                {selectedFile && (
                  <img
                    src={URL.createObjectURL(selectedFile)}
                    alt=""
                    className="img-fluid shadow-lg d-block mx-auto mb-4"
                    style={{ maxWidth: "100%", height: "150px" }}
                  />
                )}
                <p>
                  <Trans t={t} i18nKey="step4.input.description">
                    <strong>
                      {{ country: countries[info.country as keyof typeof countries].name }}
                    </strong>
                  </Trans>
                </p>
                <ul className="list">
                  <li>{t("step4.input.passport")}</li>
                  <li>{t("step4.input.drivers_license")}</li>
                  <li>{t("step4.input.identity_card")}</li>
                </ul>
              </CardBody>
              <CardFooter>
                {isDragActive ? t("step4.input.files_drop") : t("step4.input.upload")}
              </CardFooter>
              <input {...getInputProps()} />
            </Card>
          )}
        </Dropzone>
        <Row>
          <Col>
            <Button outline color="black" block onClick={onBack}>
              {t("step4.back")}
            </Button>
          </Col>
          <Col>
            {!selectedFile && (
              <Button color="black" type="submit" block>
                {t("step4.skip")}
              </Button>
            )}
            {selectedFile && (
              <Button color="black" type="submit" block>
                {t("step4.continue")}
              </Button>
            )}
          </Col>
        </Row>
      </Form>
    </>
  );
};

export default Step4Document;
