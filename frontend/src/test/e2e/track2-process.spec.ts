import { expect, test } from "@playwright/test";

test("Track 2 Process Management flow recommends scheme and opens Assessment Hub", async ({ page, request }) => {
  const apiBase = process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8000/api/v1";

  // 1. Create assessment
  const created = await request.post(`${apiBase}/assessments`);
  expect(created.ok()).toBeTruthy();
  const assessmentId = (await created.json()).id as string;

  // 2. Submit business profile for Process Management
  const profile = await request.post(`${apiBase}/business-profiles`, {
    data: {
      name: "Track 2 Food Factory",
      business_type: "formal",
      scale: "medium",
      market: ["export"],
      existing_certifications: ["SLS_GMP"],
      has_food_licence: "yes",
      assessment_id: assessmentId,
    },
  });
  expect(profile.ok()).toBeTruthy();

  // 3. Open Process Management certificates page
  await page.goto(`/process-management/${assessmentId}/certificates`);
  await expect(page.getByRole("heading", { name: "Your applicable certifications" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Certification pathway")).toBeVisible();

  // 4. Click start assessment -> Hub
  await page.getByRole("link", { name: /Start assessment for/ }).click();
  await expect(page.getByRole("heading", { name: "Assessment Hub" })).toBeVisible();
});
