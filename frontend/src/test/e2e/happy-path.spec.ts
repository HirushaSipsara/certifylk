import { expect, test } from "@playwright/test";

test("one-click chilli-paste workflow reaches a complete readiness result", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Load Sample Assessment" }).click();
  await expect(page.getByRole("heading", { name: "Your readiness roadmap" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Readiness score")).toBeVisible();
  await expect(page.getByText("Confirmed strengths")).toBeVisible();
  await expect(page.getByText("Possible gaps")).toBeVisible();
  await expect(page.getByText(/LKR/).first()).toBeVisible();
  await expect(page.getByText(/does not issue, guarantee, or replace SLS certification/i)).toBeVisible();
});

test("manual evidence analysis shows actual provider, unclear polarity and confidence", async ({ page, request }, testInfo) => {
  const apiBase = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const created = await request.post(`${apiBase}/assessments`);
  expect(created.ok()).toBeTruthy();
  const assessmentId = (await created.json()).id as string;

  const profile = await request.put(`${apiBase}/assessments/${assessmentId}/profile`, {
    data: {
      product_name: "Synthetic chilli paste evidence test",
      food_category: "processed_food",
      production_location: "home_kitchen",
      production_scale: "small",
      worker_range: "1_5",
      packaging_type: "glass_bottle",
      storage_method: "room_temperature",
      shelf_life_range: "one_to_six_months",
      existing_certification: "none",
      production_record_frequency: "sometimes",
      additional_information: "Synthetic browser test only.",
    },
  });
  expect(profile.ok()).toBeTruthy();
  const adaptive = await request.post(`${apiBase}/assessments/${assessmentId}/adaptive-plan`);
  const adaptiveQuestions = (await adaptive.json()).questions as Array<{
    id: string;
    options: Array<{ value: string }>;
  }>;
  const processResponse = await request.put(`${apiBase}/assessments/${assessmentId}/process`, {
    data: {
      steps: ["Buy ingredients", "Wash ingredients", "Cook", "Fill bottles", "Store"],
      adaptive_answers: adaptiveQuestions.map((question) => ({
        question_id: question.id,
        value: question.options[0].value,
        other_text: null,
      })),
    },
  });
  expect(processResponse.ok()).toBeTruthy();
  const processAnalysis = await request.post(`${apiBase}/assessments/${assessmentId}/process-analysis`);
  expect(["gemini", "mock"]).toContain((await processAnalysis.json()).provider);
  const evidencePlan = await request.post(`${apiBase}/assessments/${assessmentId}/evidence-plan`);
  const evidenceRequests = (await evidencePlan.json()).requests as Array<{
    id: string;
    evidence_type: string;
  }>;
  const packagingArea = evidenceRequests.find((item) => item.evidence_type === "packaging_area");
  expect(packagingArea).toBeTruthy();
  const upload = await request.post(`${apiBase}/assessments/${assessmentId}/evidence/upload`, {
    multipart: {
      evidence_request_id: packagingArea!.id,
      file: {
        name: "packaging-area.png",
        mimeType: "image/png",
        buffer: Buffer.from("89504e470d0a1a0a73796e746865746963", "hex"),
      },
    },
  });
  expect(upload.ok()).toBeTruthy();
  for (const evidenceRequest of evidenceRequests.filter((item) => item.id !== packagingArea!.id)) {
    const unavailable = await request.put(`${apiBase}/assessments/${assessmentId}/evidence/${evidenceRequest.id}/unavailable`);
    expect(unavailable.ok()).toBeTruthy();
  }

  await page.goto(`/assessment/${assessmentId}/evidence`);
  const analysisResponsePromise = page.waitForResponse((response) =>
    response.url().endsWith(`/assessments/${assessmentId}/evidence-analysis`),
  );
  await page.getByRole("button", { name: "Analyze evidence" }).click();
  const analysisBody = await (await analysisResponsePromise).json() as {
    provider?: "gemini" | "mock";
    fallback_used?: boolean;
  };
  await expect(page.getByRole("heading", { name: "Evidence analysis complete" })).toBeVisible();
  const expectedProviderLabel = analysisBody.fallback_used
    ? "Completed using fallback analysis"
    : analysisBody.provider === "gemini"
      ? "Analyzed by Gemini"
      : "Analyzed by Mock AI";
  await expect(page.getByLabel("AI analysis provider")).toHaveText(expectedProviderLabel);
  await expect(page.getByLabel("Polarity: Unclear")).toBeVisible();
  await expect(page.getByText("Confidence: Unclear (45%)")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("evidence-analysis-review.png"), fullPage: true });
});
