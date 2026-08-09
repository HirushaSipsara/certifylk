import { expect, test } from "@playwright/test";

test("Track 1 Fresh Fruit Cordial journey reaches completed readiness report", async ({ page, request }) => {
  const apiBase = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8000/api/v1";

  // 1. Create assessment
  const created = await request.post(`${apiBase}/assessments`);
  expect(created.ok()).toBeTruthy();
  const assessmentId = (await created.json()).id as string;

  // 2. Submit business profile for Fresh Fruit Cordial
  const profile = await request.post(`${apiBase}/business-profiles`, {
    data: {
      name: "Fresh Fruit Cordial Enterprise",
      business_type: "formal",
      scale: "small",
      market: ["supermarket"],
      existing_certifications: [],
      has_food_licence: "yes",
      assessment_id: assessmentId,
      product_slug: "fresh_fruit_cordial",
    },
  });
  expect(profile.ok()).toBeTruthy();

  // 3. Open applicability certificates page
  await page.goto(`/product-quality/${assessmentId}/certificates`);
  await expect(page.getByRole("heading", { name: "Your applicable certificates" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Recommended starting point")).toBeVisible();

  // 4. Click start assessment -> Hub
  await page.getByRole("link", { name: /Start assessment for/ }).click();
  await page.waitForURL(/\/assessment\/[^/]+\/hub$/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Track your readiness progress" })).toBeVisible();

  // 5. Navigate to requirements
  await page.getByRole("link", { name: /View requirements/ }).click();
  await page.waitForURL(/\/assessment\/[^/]+\/hub\/requirements$/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "Scheme Requirements" })).toBeVisible();
  await expect(page.getByText("Content not independently verified")).toBeVisible();
});
