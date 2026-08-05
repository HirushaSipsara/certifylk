import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import ProfilePage from "@/app/assessment/[assessmentId]/profile/page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ assessmentId: "00000000-0000-0000-0000-000000000001" }),
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/hooks/useAssessment", () => ({
  useAssessment: () => ({
    assessment: null,
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

test("profile reveals the conditional Other field", async () => {
  const user = userEvent.setup();
  render(<ProfilePage />);
  expect(screen.queryByLabelText("Other food category")).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText("Food category"), "other");
  expect(screen.getByLabelText("Other food category")).toBeInTheDocument();
});
