import { render, screen } from "@testing-library/react";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { EvidenceObservationList } from "@/components/EvidenceObservationList";
import type { EvidenceObservation } from "@/types";

test("provider label uses confirmed response metadata and tolerates missing metadata", () => {
  const { rerender } = render(<AIAnalysisStatus provider="gemini" fallback_used={false} />);
  expect(screen.getByLabelText("AI analysis provider")).toHaveTextContent("Analyzed by Gemini");

  rerender(<AIAnalysisStatus provider="mock" fallback_used />);
  expect(screen.getByLabelText("AI analysis provider")).toHaveTextContent("Completed using fallback analysis");
  expect(screen.queryByText("Analyzed by Gemini")).not.toBeInTheDocument();

  rerender(<AIAnalysisStatus provider="mock" fallback_used={false} />);
  expect(screen.getByLabelText("AI analysis provider")).toHaveTextContent("Analyzed by Mock AI");

  rerender(<AIAnalysisStatus />);
  expect(screen.queryByLabelText("AI analysis provider")).not.toBeInTheDocument();
});

test("evidence observations show polarity icons, text labels, and confidence bands", () => {
  const observations: EvidenceObservation[] = [
    {
      id: "supports",
      evidence_request_id: "request-1",
      requirement_id: "HYG_HANDWASH",
      polarity: "supports",
      text: "A handwashing area is visible.",
      confidence: 0.8,
      provider: "gemini",
      fallback_used: false,
      validation_status: "validated",
    },
    {
      id: "concern",
      evidence_request_id: "request-2",
      requirement_id: "HYG_CHEMICAL",
      polarity: "concern",
      text: "Cleaning chemicals appear beside ingredients.",
      confidence: 0.79,
      provider: "mock",
      fallback_used: true,
      validation_status: "validated",
    },
    {
      id: "unclear",
      evidence_request_id: "request-3",
      requirement_id: "PACK_LABEL",
      polarity: "unclear",
      text: "The label text cannot be read clearly.",
      confidence: 0.49,
    },
  ];

  render(<EvidenceObservationList observations={observations} />);

  expect(screen.getByText("Supports")).toBeInTheDocument();
  expect(screen.getByText("Concern")).toBeInTheDocument();
  expect(screen.getAllByText("Unclear").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByLabelText("Polarity: Supports")).toBeInTheDocument();
  expect(screen.getByLabelText("Polarity: Concern")).toBeInTheDocument();
  expect(screen.getByLabelText("Polarity: Unclear")).toBeInTheDocument();
  expect(screen.getByText("Confidence: Clear (80%)")).toBeInTheDocument();
  expect(screen.getByText("Confidence: Plausible (79%)")).toBeInTheDocument();
  expect(screen.getByText("Confidence: Unclear (49%)")).toBeInTheDocument();
  expect(screen.getByText("✓")).toHaveAttribute("aria-hidden", "true");
  expect(screen.getByText("!")).toHaveAttribute("aria-hidden", "true");
  expect(screen.getAllByText("?")[0]).toHaveAttribute("aria-hidden", "true");
  expect(screen.getByText("Analyzed by Gemini")).toBeInTheDocument();
  expect(screen.getByText("Completed using fallback analysis")).toBeInTheDocument();
  expect(screen.getAllByText("Structured output validated")).toHaveLength(2);
});

test("unknown evidence polarity receives a neutral defensive presentation", () => {
  render(
    <EvidenceObservationList
      observations={[{
        id: "future-polarity",
        evidence_request_id: "request-4",
        requirement_id: "DOC_BATCH",
        polarity: "future_value",
        text: "A future API value is shown safely.",
        confidence: 0.9,
      }]}
    />,
  );

  expect(screen.getByText("Observation")).toBeInTheDocument();
  expect(screen.getByText("?")).toHaveAttribute("aria-hidden", "true");
  expect(screen.getByText("A future API value is shown safely.")).toBeInTheDocument();
});
