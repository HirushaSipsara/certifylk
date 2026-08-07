import { render, screen } from "@testing-library/react";

import { CostBreakdownTable } from "@/components/CostBreakdownTable";
import { CostRange } from "@/components/CostRange";
import { RoadmapChecklist } from "@/components/RoadmapChecklist";
import type { RoadmapItem } from "@/types";

test("CostBreakdownTable renders each canonical cost type and handles quote-required vs numeric costs", () => {
  render(
    <CostBreakdownTable
      summary={{
        one_time_min: 50000,
        one_time_max: 80000,
        recurring_min: 20000,
        recurring_max: 30000,
        currency: "LKR",
        by_type: {
          certifying_body_fee: {
            one_time_min: 50000,
            one_time_max: 80000,
            recurring_min: 20000,
            recurring_max: 30000,
            items_count: 1,
          },
          lab_testing_fee: {
            one_time_min: 0,
            one_time_max: 0,
            recurring_min: 0,
            recurring_max: 0,
            items_count: 1,
          },
          business_capex: {
            one_time_min: 0,
            one_time_max: 0,
            recurring_min: 0,
            recurring_max: 0,
            items_count: 1,
          },
          business_opex: {
            one_time_min: 0,
            one_time_max: 0,
            recurring_min: 0,
            recurring_max: 0,
            items_count: 0,
          },
        },
      }}
    />
  );

  expect(screen.getByText("Certification Body Fee")).toBeInTheDocument();
  expect(screen.getByText("Laboratory Testing Fee")).toBeInTheDocument();
  expect(screen.getByText("Business Capex")).toBeInTheDocument();
  expect(screen.getByText("Business Opex")).toBeInTheDocument();

  // Known numeric range
  expect(screen.getByText(/Rs. 50,000 – 80,000/)).toBeInTheDocument();
  // Quote required text instead of 0-0
  expect(screen.getAllByText("Quote required / Included").length).toBeGreaterThan(0);
});

test("CostRange renders 'Quote required' when quoteRequired is true and 'Included' for legitimate zero cost", () => {
  const { rerender } = render(
    <CostRange
      label="One-time"
      range={{ min: 0, max: 0, currency: "LKR" }}
      quoteRequired={true}
    />
  );
  expect(screen.getByText("Quote required")).toBeInTheDocument();
  expect(screen.queryByText(/LKR 0–0/)).not.toBeInTheDocument();

  rerender(
    <CostRange
      label="One-time"
      range={{ min: 0, max: 0, currency: "LKR" }}
      quoteRequired={false}
    />
  );
  expect(screen.getByText("Included / No extra fee")).toBeInTheDocument();
});

test("RoadmapChecklist displays cost_type badge, expected gain, projected score, source notes, effective date, and review date", () => {
  const item: RoadmapItem = {
    recommendation_id: "rec_1",
    title: "Install Stainless Steel Handwash Basin",
    implementation_steps: ["Purchase sink", "Install plumbing"],
    priority: 1,
    cost_type: "business_capex",
    one_time_cost: { min: 25000, max: 40000, currency: "LKR" },
    recurring_cost: { min: 0, max: 0, currency: "LKR" },
    cost_note: "Local plumbing hardware catalog price.",
    effective_date: "2026-01-01",
    last_reviewed: "2026-08-01",
    quote_required: false,
    expected_gain: 6.0,
    projected_score: 58,
    explanation: "Improves plant hygiene and satisfies SLS requirement.",
  };

  render(<RoadmapChecklist items={[item]} />);

  expect(screen.getByText("Install Stainless Steel Handwash Basin")).toBeInTheDocument();
  expect(screen.getByText("Business Capex")).toBeInTheDocument();
  expect(screen.getByText(/Expected readiness gain: \+6\.0/)).toBeInTheDocument();
  expect(screen.getByText(/projected score after this item: 58\/100/)).toBeInTheDocument();
  expect(screen.getByText(/Effective 2026-01-01/)).toBeInTheDocument();
  expect(screen.getByText(/Reviewed 2026-08-01/)).toBeInTheDocument();
});
