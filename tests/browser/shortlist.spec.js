// SYS-4419 — Figure 4 maintenance review shortlist: behaviour in a real browser.
const { test, expect } = require("@playwright/test");
const {
  MIXED_FLEET,
  CLEAN_FLEET,
  subsystem,
  platform,
  largeFleet,
  mockPlatforms,
  withMarking,
  openDashboard,
  waitForShortlist,
} = require("./fixtures");

const THRESHOLD_LABEL = "Review threshold, degrees Celsius (°C)";

async function loadFleet(page, fleet) {
  await mockPlatforms(page, { json: fleet });
  await openDashboard(page);
  await waitForShortlist(page);
}

async function setThreshold(page, value) {
  const input = page.getByLabel(THRESHOLD_LABEL);
  await input.fill(value);
  await input.blur();
}

function rowFor(page, platformId) {
  return page.locator("#review-list > li", { has: page.locator(".review__id", { hasText: platformId }) });
}

test.describe("reviewReasons — pure classifier (browser unit)", () => {
  test.beforeEach(async ({ page }) => {
    await loadFleet(page, CLEAN_FLEET);
  });

  test("threshold boundary at 78.0 °C: 77.9 excluded, 78.0 and 78.1 included", async ({ page }) => {
    const result = await page.evaluate(() => {
      const codes = (t) => window.FleetReview.reviewReasons(
        { platformId: "X", designation: "X", platformType: "AIR", operational: true,
          subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: t, operational: true }] },
        78.0,
      ).map((r) => r.code);
      return { below: codes(77.9), at: codes(78.0), above: codes(78.1) };
    });
    expect(result.below).toEqual([]);
    expect(result.at).toEqual(["AT_OR_ABOVE_THRESHOLD"]);
    expect(result.above).toEqual(["AT_OR_ABOVE_THRESHOLD"]);
  });

  test("missing reading is never zero and never passes a 0 °C threshold", async ({ page }) => {
    const codes = await page.evaluate(() => window.FleetReview.reviewReasons(
      { platformId: "X", designation: "X", platformType: "LAND", operational: true,
        subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: null, operational: true }] },
      0,
    ).map((r) => r.code));
    expect(codes).toEqual(["READING_UNAVAILABLE"]);
  });

  test("non-numeric and non-finite readings are unavailable, not measured", async ({ page }) => {
    const result = await page.evaluate(() => {
      const codes = (t) => window.FleetReview.reviewReasons(
        { platformId: "X", designation: "X", platformType: "LAND", operational: true,
          subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: t, operational: true }] },
        10,
      ).map((r) => r.code);
      return { text: codes("hot"), nan: codes(NaN), inf: codes(Infinity), missing: codes(undefined) };
    });
    expect(result.text).toEqual(["MALFORMED_RECORD", "READING_UNAVAILABLE"]);
    expect(result.nan).toContain("READING_UNAVAILABLE");
    expect(result.nan).not.toContain("AT_OR_ABOVE_THRESHOLD");
    expect(result.inf).toContain("READING_UNAVAILABLE");
    expect(result.inf).not.toContain("AT_OR_ABOVE_THRESHOLD");
    expect(result.missing).toEqual(["MALFORMED_RECORD", "READING_UNAVAILABLE"]);
  });

  test("combined reasons are all returned, in display precedence", async ({ page }) => {
    const codes = await page.evaluate(() => window.FleetReview.reviewReasons(
      { platformId: "X", designation: "X", platformType: "MISSION_SYSTEM", operational: false,
        subsystems: [
          { subsystemId: "A", name: "A", temperatureCelsius: 94, operational: false },
          { subsystemId: "B", name: "B", temperatureCelsius: null, operational: true },
        ] },
      78,
    ).map((r) => r.code));
    expect(codes).toEqual([
      "PLATFORM_NOT_OPERATIONAL",
      "SUBSYSTEM_NOT_OPERATIONAL",
      "READING_UNAVAILABLE",
      "AT_OR_ABOVE_THRESHOLD",
    ]);
  });

  test("malformed records, unknown types and empty subsystem lists get data-unavailable reasons", async ({ page }) => {
    const result = await page.evaluate(() => {
      const codes = (r) => window.FleetReview.reviewReasons(r, 50).map((x) => x.code);
      return {
        nullRecord: codes(null),
        stringRecord: codes("LND-1"),
        noSubsystems: codes({ platformId: "X", designation: "X", platformType: "AIR", operational: true, subsystems: [] }),
        unknownType: codes({ platformId: "X", designation: "X", platformType: "SEA", operational: true,
          subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: 1, operational: true }] }),
        missingFields: codes({ platformId: "X", platformType: "LAND" }),
        nonBooleanFlag: codes({ platformId: "X", designation: "X", platformType: "LAND", operational: "yes",
          subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: 1, operational: true }] }),
      };
    });
    expect(result.nullRecord).toEqual(["MALFORMED_RECORD", "UNRECOGNISED_TYPE"]);
    expect(result.stringRecord).toEqual(["MALFORMED_RECORD", "UNRECOGNISED_TYPE"]);
    expect(result.noSubsystems).toEqual(["NO_SUBSYSTEMS"]);
    expect(result.unknownType).toEqual(["UNRECOGNISED_TYPE"]);
    expect(result.missingFields).toEqual(["MALFORMED_RECORD"]);
    expect(result.nonBooleanFlag).toEqual(["MALFORMED_RECORD"]);
  });

  test("temperature rule is inactive without a valid threshold", async ({ page }) => {
    const codes = await page.evaluate(() => window.FleetReview.reviewReasons(
      { platformId: "X", designation: "X", platformType: "AIR", operational: true,
        subsystems: [{ subsystemId: "S", name: "S", temperatureCelsius: 149, operational: true }] },
      null,
    ).map((r) => r.code));
    expect(codes).toEqual([]);
  });

  test("parseThreshold accepts 0 to 150 °C at one decimal and rejects everything else", async ({ page }) => {
    const result = await page.evaluate(() => {
      const p = (v) => window.FleetReview.parseThreshold(v);
      const accept = ["0", "150", "78", "78.0", " 78.1 ", "0.0", "149.9", "0.1"].map((v) => [v, p(v)]);
      const reject = ["", "   ", "-0.1", "150.1", "151", "1.25", "NaN", "Infinity", "-Infinity", "1e2",
        "abc", "78.", ".5", "7 8"].map((v) => [v, p(v)]);
      const numeric = [NaN, Infinity, -Infinity].map((v) => [String(v), p(v)]);
      return { accept, reject, numeric };
    });
    for (const [raw, parsed] of result.accept) {
      expect(parsed.ok, `accepts ${JSON.stringify(raw)}`).toBe(true);
    }
    expect(result.accept.map(([, parsed]) => parsed.value)).toEqual([0, 150, 78, 78, 78.1, 0, 149.9, 0.1]);
    for (const [raw, parsed] of result.reject) {
      expect(parsed.ok, `rejects ${JSON.stringify(raw)}`).toBe(false);
      expect(parsed.message).toMatch(/threshold/i);
    }
    const codes = Object.fromEntries(result.reject.map(([raw, parsed]) => [raw, parsed.code]));
    expect(codes[""]).toBe("REQUIRED");
    expect(codes["-0.1"]).toBe("RANGE");
    expect(codes["150.1"]).toBe("RANGE");
    expect(codes["1.25"]).toBe("FORMAT");
    expect(codes["NaN"]).toBe("NON_FINITE");
    expect(codes["Infinity"]).toBe("NON_FINITE");
    for (const [, parsed] of result.numeric) {
      expect(parsed.code).toBe("NON_FINITE");
    }
  });
});

test.describe("Figure 4 — filtering, reasons and threshold", () => {
  test("each shortlisted platform appears once with all of its reasons", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    await setThreshold(page, "78");

    await expect(page.locator("#review-list > li")).toHaveCount(7);
    await expect(page.locator("#review-status")).toContainText("7 of 9");
    const combined = rowFor(page, "SYN-103");
    await expect(combined).toHaveCount(1);
    await expect(combined.locator(".review__reasons li")).toHaveText([
      /Platform reports not operational/,
      /Subsystem reports not operational: GEN-01/,
      /Reading unavailable or invalid, not treated as zero: COM-01 not published/,
      /At or above review threshold 78\.0 °C: GEN-01 94 °C/,
    ]);
    await expect(rowFor(page, "SYN-101")).toContainText("GBX-01 78 °C");
    await expect(rowFor(page, "SYN-102")).toHaveCount(0);
    await expect(page.locator("#review-clear")).toContainText("SYN-102");
    await expect(page.locator("#review-clear")).toContainText("not evidence of readiness");
    await expect(rowFor(page, "SYN-104")).toContainText("SNS-01 invalid value");
    await expect(rowFor(page, "SYN-105")).toContainText("platform type not recognised: SEA");
    await expect(rowFor(page, "SYN-106")).toContainText("no subsystems published");
    await expect(rowFor(page, "SYN-107")).toContainText("does not match the published revision C shape");
    await expect(rowFor(page, "(no identifier published)")).toHaveCount(1);
  });

  test("type filter shows matching counts and narrows the shortlist", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    await setThreshold(page, "78");
    const select = page.getByLabel("Platform type");

    await expect(select.locator("option")).toHaveText([
      "All platforms (9)", "LAND (3)", "AIR (3)", "MISSION SYSTEM (1)", "Unrecognised type (2)",
    ]);
    await select.selectOption("AIR");
    await expect(page.locator("#review-status")).toContainText("2 of 3");
    await expect(page.locator("#review-status")).toContainText("filter: AIR");
    await expect(page.locator("#review-list .review__id")).toHaveText(["SYN-101", "SYN-106"]);

    await select.selectOption("UNRECOGNISED");
    await expect(page.locator("#review-list > li")).toHaveCount(2);
  });

  test("a type with no platforms shows an explicit empty state", async ({ page }) => {
    await loadFleet(page, CLEAN_FLEET);
    await setThreshold(page, "10");
    await page.getByLabel("Platform type").selectOption("MISSION_SYSTEM");

    await expect(page.locator("#review-status")).toContainText("No platforms of this type");
    await expect(page.locator("#review-status")).toContainText("0 of 0");
    await expect(page.locator("#review-list > li")).toHaveCount(0);
  });

  test("an empty shortlist is explicit and never presented as readiness", async ({ page }) => {
    await loadFleet(page, CLEAN_FLEET);
    await setThreshold(page, "150");

    await expect(page.locator("#review-status")).toContainText("Empty shortlist");
    await expect(page.locator("#review-status")).toContainText("not evidence of readiness");
    await expect(page.locator("#review-list > li")).toHaveCount(0);
  });

  test("there is no default threshold and the temperature rule starts inactive", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    const input = page.getByLabel(THRESHOLD_LABEL);

    await expect(input).toHaveValue("");
    await expect(input).toHaveAttribute("required", "");
    await expect(page.locator("#review-status")).toContainText("Temperature rule inactive");
    await expect(page.locator("#review-status")).toContainText("incomplete");
    await expect(rowFor(page, "SYN-101")).toHaveCount(0);
  });

  test("invalid threshold input shows a validation error in text", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    const input = page.getByLabel(THRESHOLD_LABEL);
    const error = page.locator("#review-threshold-error");

    for (const [raw, message] of [
      ["150.1", /must be 0 to 150 °C/],
      ["-0.1", /must be 0 to 150 °C/],
      ["1.25", /at most one decimal place/],
      ["Infinity", /non-finite/],
      ["NaN", /non-finite/],
      ["", /Threshold required/],
    ]) {
      await input.fill(raw);
      await input.blur();
      await expect(error, `input ${JSON.stringify(raw)}`).toHaveText(message);
      await expect(input).toHaveAttribute("aria-invalid", "true");
      await expect(page.getByRole("alert")).toHaveText(message);
    }

    await input.fill("0");
    await expect(error).toHaveText("");
    await expect(input).toHaveAttribute("aria-invalid", "false");
    await input.fill("150");
    await expect(error).toHaveText("");
  });

  test("missing readings are a distinct, stated condition", async ({ page }) => {
    await loadFleet(page, [platform("SYN-300", "LAND", [subsystem("A", null), subsystem("B", 20)])]);
    await setThreshold(page, "50");

    await expect(page.locator("#review-status")).toContainText("Missing readings: 1 subsystem reading is unavailable");
    await expect(rowFor(page, "SYN-300")).toContainText("A not published");
  });

  test("the published service fixture at 78 °C: AIR-207 shortlisted, LND-114 not", async ({ page }) => {
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "78");

    await expect(rowFor(page, "AIR-207")).toContainText("GBX-01 78 °C");
    await expect(rowFor(page, "LND-114")).toHaveCount(0);
    await expect(page.locator("#review-clear")).toContainText("LND-114");
  });
});

test.describe("Figure 4 — honest interpretation, safety and accessibility", () => {
  test("no readiness class is shown and retrieval is separated from observation", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    await setThreshold(page, "78");

    const body = await page.locator("body").innerText();
    expect(body).not.toMatch(/\b(FMC|PMC|NMC)\b/);
    expect(body).not.toMatch(/fully mission capable|partially mission capable|not mission capable/i);
    await expect(page.locator("#retrieved-at")).toHaveText(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC[+-]\d{2}:\d{2}$/);
    const ledger = page.locator(".retrieval__times");
    await expect(ledger).toContainText("Retrieved · this browser's clock");
    await expect(ledger).toContainText("ObservedNot published at revision C");
    await expect(ledger).toContainText("Telemetry freshnessUnknown");
    await expect(page.locator(".review__advisory")).toContainText("not a readiness classification");
  });

  test("Figure 2 draws no threshold line when a threshold is entered", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    const before = await page.locator("#measured").innerHTML();
    await setThreshold(page, "50");
    expect(await page.locator("#measured").innerHTML()).toBe(before);
  });

  test("untrusted labels render as inert text in every figure", async ({ page }) => {
    const hostile = [
      platform('<img src=x onerror="window.__xss=1">', "AIR", [
        subsystem('<script>window.__xss=2</script>', 99, false, '<svg onload="window.__xss=3">'),
      ], false, '<b onmouseover="window.__xss=4">Rotor</b>'),
      platform("SYN-X2", '<iframe src="javascript:window.__xss=5">', [subsystem("S", null)]),
    ];
    await loadFleet(page, hostile);
    await setThreshold(page, "10");

    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
    await expect(page.locator("#review-list img, #review-list script, #review-list svg, #review-list iframe, #review-list b")).toHaveCount(0);
    await expect(page.locator("#tally img, #measured img, #measured script, #measured b")).toHaveCount(0);
    await expect(page.locator("#review-list")).toContainText('<b onmouseover="window.__xss=4">Rotor</b>');
    await expect(page.locator("#review-list")).toContainText('<script>window.__xss=2</script>');
    await expect(page.locator("#review-list")).toContainText('platform type not recognised: <iframe src="javascript:window.__xss=5">');
    await page.locator("#review-list").hover();
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });

  test("reasons are carried by words, not colour", async ({ page }) => {
    await loadFleet(page, MIXED_FLEET);
    await setThreshold(page, "78");
    const reasons = page.locator("#review-list .review__reasons li");
    const count = await reasons.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i += 1) {
      const words = await reasons.nth(i).locator("span:not([aria-hidden])").innerText();
      expect(words.trim().length).toBeGreaterThan(10);
    }
    await expect(page.locator("#review-list .review__glyph").first()).toHaveAttribute("aria-hidden", "true");
  });

  test("filter, threshold and export are keyboard operable with accessible names", async ({ page }) => {
    await withMarking(page);
    await loadFleet(page, MIXED_FLEET);
    await expect(page.getByRole("combobox", { name: "Platform type" })).toBeVisible();
    await expect(page.getByRole("textbox", { name: THRESHOLD_LABEL })).toBeVisible();
    await expect(page.getByRole("button", { name: "Export displayed shortlist (CSV)" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Refresh fleet record" })).toBeVisible();

    await page.getByRole("button", { name: "Refresh fleet record" }).focus();
    for (let i = 0; i < 40; i += 1) {
      if (await page.getByLabel("Platform type").evaluate((node) => node === document.activeElement)) { break; }
      await page.keyboard.press("Tab");
    }
    await expect(page.getByLabel("Platform type")).toBeFocused();
    // Type-ahead selection behaves the same on every platform's native select.
    await page.keyboard.type("L");
    await expect(page.getByLabel("Platform type")).toHaveValue("LAND");
    await page.keyboard.press("Tab");
    await expect(page.getByLabel(THRESHOLD_LABEL)).toBeFocused();
    await page.keyboard.type("78");
    await expect(page.locator("#review-status")).toContainText("2 of 3");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "Export displayed shortlist (CSV)" })).toBeFocused();
    const [file] = await Promise.all([page.waitForEvent("download"), page.keyboard.press("Enter")]);
    expect(file.suggestedFilename()).toMatch(/^sys-4419-review-shortlist-land-/);
  });
});

test.describe("Fleet plate — load, failure and refresh states", () => {
  test("loading is distinct from every other state", async ({ page }) => {
    await mockPlatforms(page, { json: CLEAN_FLEET, delayMs: 1500 });
    await openDashboard(page);

    await expect(page.locator("#review-status")).toContainText("Reading GET /platforms");
    await expect(page.locator("#retrieved-at")).toHaveText("Retrieving…");
    await expect(page.locator("#tally .skeleton")).toHaveCount(1);
    await expect(page.getByRole("button", { name: "Export displayed shortlist (CSV)" })).toBeDisabled();
    await waitForShortlist(page);
  });

  test("API failure shows a fixed generic message without raw error detail", async ({ page }) => {
    await mockPlatforms(page, { status: 500, raw: "Traceback: internal-diagnostic-detail", contentType: "text/plain" });
    await openDashboard(page);

    await expect(page.locator("#tally")).toContainText("Fleet record unavailable");
    await expect(page.locator("#review-status")).toContainText("Fleet record unavailable");
    const body = await page.locator("body").innerText();
    expect(body).not.toContain("internal-diagnostic-detail");
    expect(body).not.toContain("HTTP 500");
    expect(body).not.toContain("Traceback");
    await expect(page.locator("#measured")).toBeEmpty();
    await expect(page.locator("#review-list > li")).toHaveCount(0);
  });

  test("network failure is reported as unavailable, not as an empty fleet", async ({ page }) => {
    await mockPlatforms(page, { abort: true });
    await openDashboard(page);

    await expect(page.locator("#tally")).toContainText("Fleet record unavailable");
    await expect(page.locator("body")).not.toContainText("No platforms published");
    expect(await page.locator("body").innerText()).not.toMatch(/Failed to fetch|TypeError/);
  });

  for (const [name, spec] of [
    ["an object instead of an array", { json: { platforms: [] } }],
    ["null", { json: null }],
    ["a body that is not JSON", { raw: "<html>proxy error</html>" }],
  ]) {
    test(`invalid response (${name}) is distinct from an empty fleet`, async ({ page }) => {
      await mockPlatforms(page, spec);
      await openDashboard(page);

      await expect(page.locator("#tally")).toContainText("Response not recognised");
      await expect(page.locator("#review-status")).toContainText("Response not recognised");
      await expect(page.locator("body")).not.toContainText("No platforms published");
      await expect(page.locator("body")).not.toContainText("proxy error");
    });
  }

  test("an empty fleet is distinct from an empty shortlist", async ({ page }) => {
    await loadFleet(page, []);
    await expect(page.locator("#tally")).toContainText("No platforms published");
    await expect(page.locator("#review-status")).toContainText("No platforms published");
    await expect(page.locator("#review-status")).toContainText("not an empty shortlist");
    await expect(page.locator("#review-status")).not.toContainText("Empty shortlist");
  });

  test("a failed refresh keeps prior data, marks it historical and offers retry", async ({ page }) => {
    let calls = 0;
    await mockPlatforms(page, () => {
      calls += 1;
      return calls === 2 ? { status: 503, raw: "down" } : { json: MIXED_FLEET };
    });
    await openDashboard(page);
    await waitForShortlist(page);
    await setThreshold(page, "78");
    const retrieved = await page.locator("#retrieved-at").innerText();

    await page.getByRole("button", { name: "Refresh fleet record" }).click();
    await expect(page.locator("#retrieval-status")).toContainText("Historical — not current");
    await expect(page.locator("#retrieval-status")).toContainText(`still shows the record retrieved at ${retrieved}`);
    await expect(page.locator("#retrieved-at")).toHaveText(`${retrieved} · historical`);
    await expect(page.locator("#review-status")).toContainText("Historical — not current");
    await expect(page.locator("#review-list > li")).toHaveCount(7);
    await expect(page.locator("#measured .row")).toHaveCount(MIXED_FLEET.length);
    await expect(page.getByRole("button", { name: "Export displayed shortlist (CSV)" })).toBeDisabled();
    await expect(page.locator("#review-export-why")).toContainText("historical after a failed refresh");

    await page.locator("#retrieval-status").getByRole("button", { name: "Retry" }).click();
    await expect(page.locator("#retrieval-status")).toBeEmpty();
    await expect(page.locator("#retrieved-at")).not.toContainText("historical");
    await expect(page.locator("#review-status")).not.toContainText("Historical");
  });

  test("retry after an initial failure recovers the fleet", async ({ page }) => {
    let calls = 0;
    await mockPlatforms(page, () => {
      calls += 1;
      return calls === 1 ? { status: 500, raw: "x" } : { json: CLEAN_FLEET };
    });
    await openDashboard(page);
    await expect(page.locator("#tally")).toContainText("Fleet record unavailable");

    await page.locator("#tally").getByRole("button", { name: "Retry" }).click();
    await waitForShortlist(page);
    await expect(page.locator("#tally")).not.toContainText("Fleet record unavailable");
    await expect(page.locator("#review-status")).toContainText("0 of 2");
  });
});

test.describe("performance — 500 synthetic platforms", () => {
  test("re-renders under 200 ms after filter and threshold changes", async ({ page }, testInfo) => {
    await loadFleet(page, largeFleet(500));

    const timings = await page.evaluate(() => {
      const input = document.getElementById("review-threshold");
      const select = document.getElementById("review-type");
      const results = [];
      const time = (label, change) => {
        const start = performance.now();
        change();
        document.getElementById("review-list").getBoundingClientRect();
        results.push({ label, ms: performance.now() - start });
      };
      ["78", "78.1", "0", "150", "42.5"].forEach((v) => time(`threshold ${v}`, () => {
        input.value = v;
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }));
      ["LAND", "AIR", "MISSION_SYSTEM", "ALL"].forEach((v) => time(`filter ${v}`, () => {
        select.value = v;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }));
      return results;
    });

    await testInfo.attach("sys-4419-performance.json", {
      body: JSON.stringify({ platforms: 500, budgetMs: 200, timings }, null, 2),
      contentType: "application/json",
    });
    console.log(`SYS-4419 performance (500 platforms, budget 200 ms): ${JSON.stringify(timings)}`);
    await expect(page.locator("#review-status")).toContainText("of 500");
    for (const { label, ms } of timings) {
      expect(ms, `${label} took ${ms.toFixed(1)} ms`).toBeLessThan(200);
    }
  });
});
