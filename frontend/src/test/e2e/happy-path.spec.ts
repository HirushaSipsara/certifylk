import { expect, test } from "@playwright/test";

test("one-click chilli-paste workflow reaches a complete readiness result", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Load Sample Report/ }).click();
  await expect(page.getByRole("heading", { name: "Your readiness roadmap" })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByText("Readiness score")).toBeVisible();
  await expect(page.getByText("Confirmed strengths")).toBeVisible();
  await expect(page.getByText("Possible gaps")).toBeVisible();
  await expect(page.getByText(/LKR/).first()).toBeVisible();
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
  await expect(page.getByText(/AI Assessment · mock · primary mode/)).toBeVisible();
  await expect(page.getByText("Recommended starting point")).toBeVisible();
  await expect(page.getByText("Source reference").first()).toBeVisible();

  await page.getByRole("link", { name: /Start assessment for/ }).click();
  await expect(page.getByRole("heading", { name: "Assessment Hub" })).toBeVisible();
  await page.getByRole("link", { name: "View requirements →" }).click();
  await expect(page.getByRole("heading", { name: "Scheme Requirements" })).toBeVisible();
  await expect(page.getByText("Content not independently verified")).toBeVisible();
  await expect(page.getByText(/Educational tool only/)).toBeVisible();
});
