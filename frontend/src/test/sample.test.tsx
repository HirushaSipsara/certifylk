import { render, screen } from "@testing-library/react";

import { ReadinessScoreCard } from "@/components/ReadinessScoreCard";
import { CostBreakdownTable } from "@/components/CostBreakdownTable";
import { DisclaimerCard } from "@/components/DisclaimerCard";

test("Canonical Fresh Fruit Cordial sample displays readiness score indicator, categorized costs, and disclaimer", () => {
  render(
    <div>
      <div data-testid="sample-badge">Sample / Demonstration</div>
      <h1>Readiness Report & Action Roadmap — Fresh Fruit Cordial (SLS Mark)</h1>
      <ReadinessScoreCard score={45} completeness={60} />
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
              quote_required_count: 0,
            },
          },
        }}
      />
      <DisclaimerCard text="CertifyLK is an educational preparation tool." />
    </div>
  );

  expect(screen.getByTestId("sample-badge")).toHaveTextContent("Sample / Demonstration");
  expect(screen.getByText(/Fresh Fruit Cordial \(SLS Mark\)/)).toBeInTheDocument();
  expect(screen.getByText("45")).toBeInTheDocument();
  expect(screen.getByText("Certification Body Fee")).toBeInTheDocument();
  expect(screen.getByText(/CertifyLK is an educational preparation tool/)).toBeInTheDocument();
});
