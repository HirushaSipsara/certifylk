import { expect, test } from "@playwright/test";

test("one-click Fresh Fruit Cordial sample reaches the readiness roadmap", async ({ page }) => {
  await page.goto("/");
  const sampleResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/assessments/sample") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: /Load Sample Report/ }).click();
  const sampleResponse = await sampleResponsePromise;
  expect(sampleResponse.ok()).toBeTruthy();
  const sample = (await sampleResponse.json()) as { result_url?: string };
  expect(sample.result_url).toMatch(/^\/assessment\/[^/]+\/result$/);
  await page.waitForURL(sample.result_url!, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Readiness Report & Action Roadmap" })).toBeVisible();
  await expect(page.getByText("Readiness Indicator")).toBeVisible();
  await expect(page.getByText("Readiness score", { exact: true })).toBeVisible();
  await expect(page.getByText("Confirmed strengths")).toBeVisible();
  await expect(page.getByText("Possible gaps")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Estimated Cost Summary (LKR)" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Prioritized Action Roadmap" })).toBeVisible();
  await expect(page.getByText(/Draft educational content/i)).toBeVisible();
  await expect(page.getByText(/does not issue, guarantee, or replace SLS certification/i)).toBeVisible();
});

test("AI applicability flow recommends a scheme and shows grounded requirements", async ({
  page,
  request,
}) => {
  const apiBase = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const created = await request.post(`${apiBase}/assessments`);
  expect(created.ok()).toBeTruthy();
  const assessmentId = (await created.json()).id as string;

  const profile = await request.post(`${apiBase}/business-profiles`, {
    data: {
      name: "Synthetic Cordial Works",
      business_type: "sole_proprietor",
      years_operating: 2,
      scale: "small",
      market: ["supermarket"],
      existing_certifications: [],
      has_food_licence: "no",
      monthly_volume_range: "100_500",
      additional_info: "Synthetic browser test only.",
      assessment_id: assessmentId,
      product_slug: "fresh_fruit_cordial",
    },
  });
  expect(profile.ok()).toBeTruthy();

  const applicabilityResponse = page.waitForResponse((response) =>
    response.url().endsWith(`/assessments/${assessmentId}/applicable-schemes`),
  );
  await page.goto(`/product-quality/${assessmentId}/certificates`);
  expect((await applicabilityResponse).ok()).toBeTruthy();

  await expect(page.getByRole("heading", { name: "Your applicable certificates" })).toBeVisible();
  await expect(page.getByText("Analyzed by Mock AI")).toBeVisible();
  await expect(page.getByText("Recommended starting point")).toBeVisible();
  await expect(page.getByText("Source reference").first()).toBeVisible();

  await page.getByRole("link", { name: /Start assessment for/ }).click();
  await page.waitForURL(/\/assessment\/[^/]+\/hub$/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Track your readiness progress" })).toBeVisible();
  await page.getByRole("link", { name: /View requirements/ }).click();
  await page.waitForURL(/\/assessment\/[^/]+\/hub\/requirements$/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Scheme Requirements" })).toBeVisible();
  await expect(page.getByText("Content not independently verified")).toBeVisible();
  await expect(page.getByText(/Educational tool only/)).toBeVisible();
});
