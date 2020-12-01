// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Button } from "reactstrap";
import { useTranslation } from "react-i18next";

const URL =
  "https://docs.google.com/forms/d/e/1FAIpQLSfHlFQ4Xz94_9c7ISzdEAPhJ6z1dBXZJ62lF8KGy8u5QoOhMw/viewform";

function Feedback() {
  const { t } = useTranslation("layout");

  return (
    <Button
      tag="a"
      size="sm"
      href={URL}
      target="_blank"
      color="black"
      className="feedback"
      title={t("feedback.title")}
    >
      <i className="fa fa-pencil" /> {t("feedback.text")}
    </Button>
  );
}

export default Feedback;
