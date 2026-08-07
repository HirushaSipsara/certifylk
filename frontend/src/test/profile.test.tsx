import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import ProfilePage from "@/app/assessment/[assessmentId]/profile/page";

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ assessmentId: "00000000-0000-0000-0000-000000000001" }),
  useRouter: () => ({ replace }),
}));

vi.mock("@/hooks/useAssessment", () => ({
  useAssessment: () => ({
    assessment: null,
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

test("legacy profile route redirects to the assessment hub", async () => {
  render(<ProfilePage />);
  expect(screen.getByText("Redirecting to your assessment hub…")).toBeInTheDocument();
  await waitFor(() =>
    expect(replace).toHaveBeenCalledWith(
      "/assessment/00000000-0000-0000-0000-000000000001/hub",
    ),
  );
});
