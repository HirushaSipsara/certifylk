import { render, screen } from "@testing-library/react";

import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { EvidenceSummary } from "@/components/EvidenceSummary";
import { ReadinessScoreCard } from "@/components/ReadinessScoreCard";
import { RoadmapChecklist } from "@/components/RoadmapChecklist";

test("result components show score, evidence groups, cost and disclaimer", () => {
  render(
    <>
      <ReadinessScoreCard score={48} completeness={55} />
      <EvidenceSummary
        strengths={[{ requirement_id: "S", title: "Clean area", status: "confirmed", rationale: "Seen", evidence_references: [] }]}
        gaps={[{ requirement_id: "G", title: "Batch records", status: "gap", rationale: "Missing", evidence_references: [] }]}
        unknowns={[]}
      />
      <RoadmapChecklist items={[{
        recommendation_id: "R",
        title: "Create batch-production record",
        implementation_steps: ["Use a template"],
        priority: 2,
        one_time_cost: { min: 0, max: 1500, currency: "LKR" },
        recurring_cost: { min: 0, max: 300, currency: "LKR" },
        cost_note: "Catalogue",
        last_reviewed: "2026-08-01",
        expected_gain: 6,
        projected_score: 54,
        explanation: "Improves traceability.",
      }]} />
      <DisclaimerCard />
    </>,
  );
  expect(screen.getByText("48")).toBeInTheDocument();
  expect(screen.getByText("Clean area")).toBeInTheDocument();
  expect(screen.getByText(/LKR 0–1,500/)).toBeInTheDocument();
  expect(screen.getByText(/does not issue, guarantee, or replace SLS certification/i)).toBeInTheDocument();
});

test("API errors are displayed accessibly", () => {
  render(<ErrorAlert message="Submitted data is invalid." />);
  expect(screen.getByRole("alert")).toHaveTextContent("Submitted data is invalid.");
});
