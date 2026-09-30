// SYS-4419 — CSV handover export: content, safety and disabled states.
const fs = require("fs");
const { test, expect } = require("@playwright/test");
const {
  TEST_MARKING,
  MIXED_FLEET,
  CLEAN_FLEET,
  subsystem,
  platform,
  mockPlatforms,
  withMarking,
  openDashboard,
  waitForShortlist,
  parseCsv,
} = require("./fixtures");

const THRESHOLD_LABEL = "Review threshold, degrees Celsius (°C)";
const EXPORT = { name: "Export displayed shortlist (CSV)" };

test.use({ timezoneId: "Australia/Perth" });

async function setThreshold(page, value) {
  const input = page.getByLabel(THRESHOLD_LABEL);
  await input.fill(value);
  await input.blur();
}

async function download(page) {
  const [file] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", EXPORT).click(),
  ]);
  const text = fs.readFileSync(await file.path(), "utf8");
  return { name: file.suggestedFilename(), text, rows: parseCsv(text.replace(/^\uFEFF/, "")) };
}

test.describe("csvCell and buildCsv — pure export functions (browser unit)", () => {
  test.beforeEach(async ({ page }) => {
    await mockPlatforms(page, { json: CLEAN_FLEET });
    await openDashboard(page);
    await waitForShortlist(page);
  });

  test("formula-leading cells are neutralised and every cell is RFC 4180 quoted", async ({ page }) => {
    const cells = await page.evaluate(() => {
      const c = window.FleetReview.csvCell;
      return {
        eq: c("=HYPERLINK(\"http://x\")"),
        plus: c("+1"),
        minus: c("-1"),
        at: c("@SUM(A1)"),
        tab: c("\t=1"),
        cr: c("\r=1"),
        comma: c("a,b"),
        quote: c('say "hi"'),
        newline: c("line 1\nline 2"),
        plain: c("LND-114"),
        empty: c(null),
        inner: c("a=b"),
      };
    });
    expect(cells.eq).toBe('"\'=HYPERLINK(""http://x"")"');
    expect(cells.plus).toBe('"\'+1"');
    expect(cells.minus).toBe('"\'-1"');
    expect(cells.at).toBe('"\'@SUM(A1)"');
    expect(cells.tab).toBe('"\'\t=1"');
    expect(cells.cr).toBe('"\'\r=1"');
    expect(cells.comma).toBe('"a,b"');
    expect(cells.quote).toBe('"say ""hi"""');
    expect(cells.newline).toBe('"line 1\nline 2"');
    expect(cells.plain).toBe('"LND-114"');
    expect(cells.empty).toBe('""');
    expect(cells.inner).toBe('"a=b"');
  });

  test("buildCsv writes marking, context, header and an explicit empty row", async ({ page }) => {
    const csv = await page.evaluate(() => {
      const FR = window.FleetReview;
      const view = FR.buildShortlist([], "AIR", 78);
      return FR.buildCsv(view, { marking: "MARK", retrievedAt: new Date(Date.UTC(2026, 8, 30, 1, 14, 2)) });
    });
    const rows = parseCsv(csv);
    expect(rows[0]).toEqual(["Handling marking", "MARK"]);
    expect(rows.find((r) => r[0] === "Platform type filter")).toEqual(["Platform type filter", "AIR"]);
    expect(rows.find((r) => r[0] === "Review threshold (°C)")[1]).toMatch(/^78\.0 °C — reviewer-selected review filter, not an operating limit$/);
    expect(rows.find((r) => r[0] === "Retrieved at")[1]).toMatch(/^2026-09-30T09:14:02\+08:00 \(this browser's clock, Australia\/Perth; time of retrieval, not observation\)$/);
    expect(rows.find((r) => r[0] === "Observed at")[1]).toContain("telemetry freshness unknown");
    expect(rows.find((r) => r[0] === "platformId")).toEqual(["platformId", "designation", "platformType", "reviewReasons"]);
    expect(rows[rows.length - 1][3]).toMatch(/^Empty shortlist: .*Not evidence of readiness\.$/);
    expect(csv).not.toMatch(/\b(FMC|PMC|NMC)\b/);
  });
});

test.describe("CSV handover export — downloaded file", () => {
  test("represents the displayed shortlist, filter context and safe cells", async ({ page }) => {
    const fleet = [
      platform("=HYPERLINK(\"http://evil\",\"x\")", "AIR", [subsystem("GBX-01", 81)], true,
        'Rotor, "rear"\nline two'),
      platform("SYN-401", "AIR", [subsystem("GBX-01", 77.9)], true, "@SUM(A1)"),
      platform("+SYN-402", "AIR", [subsystem("GBX-01", null)], true, "-cmd"),
      platform("SYN-403", "LAND", [subsystem("PWR-01", 99)]),
    ];
    await withMarking(page);
    await mockPlatforms(page, { json: fleet });
    await openDashboard(page);
    await waitForShortlist(page);
    await page.getByLabel("Platform type").selectOption("AIR");
    await setThreshold(page, "78");

    await expect(page.getByRole("button", EXPORT)).toBeEnabled();
    const displayed = await page.locator("#review-list .review__id").allInnerTexts();
    const { name, text, rows } = await download(page);

    expect(name).toMatch(/^sys-4419-review-shortlist-air-\d{8}T\d{6}\+0800\.csv$/);
    expect(text.startsWith("\uFEFF")).toBe(true);
    expect(rows[0]).toEqual(["Handling marking", TEST_MARKING]);
    expect(rows.find((r) => r[0] === "Platform type filter")[1]).toBe("AIR");
    expect(rows.find((r) => r[0] === "Review threshold (°C)")[1]).toMatch(/^78\.0 °C/);
    expect(rows.find((r) => r[0] === "Retrieved at")[1]).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00 \(this browser's clock, Australia\/Perth;/);
    expect(rows.find((r) => r[0] === "Shortlisted")[1]).toBe("2 of 3 matching platforms");

    const header = rows.findIndex((r) => r[0] === "platformId");
    const data = rows.slice(header + 1);
    expect(data.map((r) => r[0].replace(/^'/, ""))).toEqual(displayed);
    expect(data.every((r) => r.length === 4)).toBe(true);

    const formula = data.find((r) => r[0].includes("HYPERLINK"));
    expect(formula[0]).toBe("'=HYPERLINK(\"http://evil\",\"x\")");
    expect(formula[1]).toBe('Rotor, "rear"\nline two');
    expect(formula[3]).toContain("At or above review threshold 78.0 °C: GBX-01 81 °C");
    const plus = data.find((r) => r[0].includes("SYN-402"));
    expect(plus[0]).toBe("'+SYN-402");
    expect(plus[1]).toBe("'-cmd");
    expect(plus[3]).toContain("not treated as zero");
    for (const row of rows) {
      for (const cell of row) {
        expect(cell, `cell ${JSON.stringify(cell)}`).not.toMatch(/^[=+\-@\t\r]/);
      }
    }
    expect(text).not.toContain("SYN-401");
    expect(text).not.toContain("SYN-403");
  });

  test("an empty shortlist exports an explicit empty row, never a blank file", async ({ page }) => {
    await withMarking(page);
    await mockPlatforms(page, { json: CLEAN_FLEET });
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "150");

    await expect(page.locator("#review-export-why")).toContainText("explicit empty shortlist");
    const { rows } = await download(page);
    expect(rows.find((r) => r[0] === "Shortlisted")[1]).toBe("0 of 2 matching platforms");
    expect(rows[rows.length - 1][3]).toContain("Not evidence of readiness");
  });

  test("combined reasons stay in one row, separated by line breaks", async ({ page }) => {
    await withMarking(page);
    await mockPlatforms(page, { json: MIXED_FLEET });
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "78");

    const { rows } = await download(page);
    const combined = rows.filter((r) => r[0] === "SYN-103");
    expect(combined).toHaveLength(1);
    expect(combined[0][3].split("\n")).toHaveLength(4);
  });
});

test.describe("CSV handover export — disabled states", () => {
  test("stays disabled while no data-owner-approved handling marking is configured", async ({ page }) => {
    await mockPlatforms(page, { json: MIXED_FLEET });
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "78");

    await expect(page.getByRole("button", EXPORT)).toBeDisabled();
    await expect(page.locator("#review-export-why")).toContainText("data owner has not yet approved the handling marking");
  });

  test("disabled without a valid threshold", async ({ page }) => {
    await withMarking(page);
    await mockPlatforms(page, { json: MIXED_FLEET });
    await openDashboard(page);
    await waitForShortlist(page);

    await expect(page.getByRole("button", EXPORT)).toBeDisabled();
    await expect(page.locator("#review-export-why")).toContainText("enter a valid review threshold first");
    await setThreshold(page, "150.1");
    await expect(page.getByRole("button", EXPORT)).toBeDisabled();
    await setThreshold(page, "150");
    await expect(page.getByRole("button", EXPORT)).toBeEnabled();
  });

  test("disabled after a failed refresh and re-enabled only by a successful one", async ({ page }) => {
    let calls = 0;
    await withMarking(page);
    await mockPlatforms(page, () => {
      calls += 1;
      return calls === 2 ? { status: 500, raw: "x" } : { json: MIXED_FLEET };
    });
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "78");
    await expect(page.getByRole("button", EXPORT)).toBeEnabled();

    await page.getByRole("button", { name: "Refresh fleet record" }).click();
    await expect(page.locator("#retrieval-status")).toContainText("Historical");
    await expect(page.getByRole("button", EXPORT)).toBeDisabled();
    await expect(page.locator("#review-export-why")).toContainText("historical after a failed refresh");

    await page.locator("#retrieval-status").getByRole("button", { name: "Retry" }).click();
    await expect(page.getByRole("button", EXPORT)).toBeEnabled();
  });

  for (const [name, spec, reason] of [
    ["API failure", { status: 500, raw: "x" }, "no fleet record was retrieved"],
    ["invalid response", { json: { not: "an array" } }, "no fleet record was retrieved"],
    ["empty fleet", { json: [] }, "the retrieved fleet is empty"],
  ]) {
    test(`disabled on ${name}`, async ({ page }) => {
      await withMarking(page);
      await mockPlatforms(page, spec);
      await openDashboard(page);
      await expect(page.locator("#review-export-why")).toContainText(reason);
      await setThreshold(page, "78");
      await expect(page.getByRole("button", EXPORT)).toBeDisabled();
    });
  }

  test("disabled while loading", async ({ page }) => {
    await withMarking(page);
    await mockPlatforms(page, { json: CLEAN_FLEET, delayMs: 1500 });
    await openDashboard(page);
    await expect(page.locator("#review-export-why")).toContainText("no fleet record retrieved yet");
    await expect(page.getByRole("button", EXPORT)).toBeDisabled();
  });
});
