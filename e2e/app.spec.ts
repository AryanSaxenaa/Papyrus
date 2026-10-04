import { expect, test } from "@playwright/test";

async function dismissShepherdIfPresent(page: import("@playwright/test").Page) {
  const prompt = page.getByTestId("shepherd-mode-prompt");
  if (await prompt.isVisible().catch(() => false)) {
    await page.getByRole("button", { name: "No thanks" }).click();
  }
}

test.describe("Papyrus app shell", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("papyrus.shepherd.declined", "1");
    });
  });

  test("upload card and replay flow open witness drawer", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");
    await dismissShepherdIfPresent(page);

    await expect(page.getByTestId("app-upload-card")).toBeVisible({ timeout: 60_000 });

    const configRes = await page.request.get("/api/config");
    expect(configRes.ok()).toBeTruthy();
    const config = (await configRes.json()) as { mode?: string };

    if (config.mode === "replay") {
      await expect(page.getByTestId("replay-banner")).toBeVisible();
    }

    const replayBtn = page.getByTestId("replay-recorded-audit").or(
      page.getByRole("button", { name: "Replay a recorded audit" }),
    );
    await replayBtn.click();

    await expect.poll(async () => {
      const audits = await page.request.get("/api/audits/summaries");
      if (!audits.ok()) return "";
      const rows = (await audits.json()) as Array<{ status?: string }>;
      const latest = rows[0];
      return latest?.status ?? "";
    }).toMatch(/complete|failed/);

    const heatmapCell = page.locator("[data-citation-id]").first();
    await expect(heatmapCell).toBeVisible({ timeout: 60_000 });
    await heatmapCell.click();
    await expect(page.getByTestId("witness-matrix")).toBeVisible();
  });

  test("DOI tab accepts input in live demo mode", async ({ page }) => {
    await page.goto("/app");
    await page.waitForLoadState("networkidle");
    await dismissShepherdIfPresent(page);

    const doiTab = page.getByRole("tab", { name: "DOI" });
    await expect(doiTab).toBeVisible({ timeout: 60_000 });
    await doiTab.click();
    await page.getByPlaceholder("10.1038/nature12373").fill("10.1038/nature12373");
    await expect(page.getByRole("button", { name: "Start audit" })).toBeEnabled();
  });
});
