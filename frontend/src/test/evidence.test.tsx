import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { EvidenceUploadCard } from "@/components/EvidenceUploadCard";

test("evidence card supports marking an item unavailable", async () => {
  const user = userEvent.setup();
  const unavailable = vi.fn().mockResolvedValue(undefined);
  render(
    <EvidenceUploadCard
      request={{
        id: "request-1",
        evidence_type: "product_label",
        kind: "document",
        title: "Product label",
        required: false,
        status: "requested",
        requirement_id: "SLS_DOC_BATCH",
        current_state_question: "Do you keep a record for every batch?",
        self_assessment: null,
        display_order: 1,
      }}
      busy={false}
      onUpload={vi.fn()}
      onUnavailable={unavailable}
      onSelfAssessment={vi.fn()}
    />,
  );
  await user.click(screen.getByRole("button", { name: "I do not have this evidence" }));
  expect(unavailable).toHaveBeenCalledOnce();
});

test("evidence card saves a controlled self-assessment without requiring a file", async () => {
  const user = userEvent.setup();
  const saveCurrentState = vi.fn().mockResolvedValue(undefined);
  render(
    <EvidenceUploadCard
      request={{
        id: "request-2",
        evidence_type: "handwashing",
        kind: "photo",
        title: "Handwashing facilities",
        required: true,
        status: "requested",
        requirement_id: "SLS_HYG_HANDWASH",
        current_state_question:
          "Do you have running water, soap and hygienic hand drying?",
        self_assessment: null,
        display_order: 2,
      }}
      busy={false}
      onUpload={vi.fn()}
      onUnavailable={vi.fn()}
      onSelfAssessment={saveCurrentState}
    />,
  );

  await user.click(screen.getByRole("button", { name: "Yes / implemented" }));
  expect(saveCurrentState).toHaveBeenCalledWith("yes");
  expect(screen.getByText("Supporting evidence (optional)")).toBeVisible();
});
