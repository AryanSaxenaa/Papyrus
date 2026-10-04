import { expect, test } from "@playwright/test";

test.describe("Shepherd mode", () => {
  test.use({
    storageState: undefined,
  });

  test("opt-in loads real replay audit and keeps it after skip", async ({ page, context }) => {
    await context.clearCookies();
    await page.addInitScript(() => {
      localStorage.removeItem("papyrus.shepherd.declined");
      localStorage.removeItem("papyrus.shepherd.completed");
    });

    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    const prompt = page.getByTestId("shepherd-mode-prompt");
    await expect(prompt).toBeVisible({ timeout: 60_000 });

    await page.getByRole("button", { name: "Start guided tour" }).click();
    await expect(page.getByTestId("current-audit-card")).toBeVisible({ timeout: 90_000 });

    const shepherdText = page.locator(".shepherd-text");
    if (await shepherdText.count()) {
      await page.locator(".shepherd-cancel-icon").click({ timeout: 5_000 }).catch(() => {});
    }

    await expect(page.getByTestId("current-audit-card")).toBeVisible();
    await expect(prompt).not.toBeVisible();
  });
});
