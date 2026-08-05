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
        display_order: 1,
      }}
      busy={false}
      onUpload={vi.fn()}
      onUnavailable={unavailable}
    />,
  );
  await user.click(screen.getByRole("button", { name: "I do not have this" }));
  expect(unavailable).toHaveBeenCalledOnce();
});
