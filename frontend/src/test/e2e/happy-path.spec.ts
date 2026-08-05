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
