// SYS-4419 — synthetic fixtures and helpers for the browser suite.
// Every record here is authored for testing. None is read from, or written
// to, src/repository.py, so the MSN-330 contract-gap fixture is untouched.

const TEST_MARKING = "TEST MARKING - synthetic value for automated tests, not approved wording";

function subsystem(id, temperatureCelsius, operational = true, name = `Subsystem ${id}`) {
  return { subsystemId: id, name, temperatureCelsius, operational };
}

function platform(id, platformType, subsystems, operational = true, designation = `Synthetic ${id}`) {
  return { platformId: id, designation, platformType, operational, subsystems };
}

// A mixed synthetic fleet covering every review rule.
const MIXED_FLEET = [
  platform("SYN-100", "LAND", [subsystem("PWR-01", 40), subsystem("HYD-01", 51)]),
  platform("SYN-101", "AIR", [subsystem("GBX-01", 78.0), subsystem("AVN-01", 42)]),
  platform("SYN-102", "AIR", [subsystem("GBX-01", 77.9)]),
  platform("SYN-103", "MISSION_SYSTEM", [
    subsystem("GEN-01", 94, false),
    subsystem("COM-01", null),
  ], false),
  platform("SYN-104", "LAND", [subsystem("SNS-01", "hot")]),
  platform("SYN-105", "SEA", [subsystem("ENG-01", 30)]),
  platform("SYN-106", "AIR", []),
  { platformId: "SYN-107", designation: "Synthetic malformed 107", platformType: "LAND" },
  null,
];

const CLEAN_FLEET = [
  platform("SYN-200", "LAND", [subsystem("PWR-01", 20)]),
  platform("SYN-201", "AIR", [subsystem("GBX-01", 30)]),
];

function largeFleet(count) {
  const types = ["LAND", "AIR", "MISSION_SYSTEM"];
  const fleet = [];
  for (let i = 0; i < count; i += 1) {
    const subs = [];
    for (let j = 0; j < 4; j += 1) {
      const t = (i * 37 + j * 11) % 131;
      subs.push(subsystem(`S${j}`, i % 97 === 0 && j === 0 ? null : t + 0.5, !(i % 53 === 0 && j === 1)));
    }
    fleet.push(platform(`PERF-${String(i).padStart(4, "0")}`, types[i % 3], subs, i % 71 !== 0));
  }
  return fleet;
}

async function mockPlatforms(page, responder) {
  await page.route("**/platforms", async (route) => {
    const spec = typeof responder === "function" ? await responder() : responder;
    if (spec.abort) {
      await route.abort("failed");
      return;
    }
    if (spec.delayMs) {
      await new Promise((resolve) => setTimeout(resolve, spec.delayMs));
    }
    await route.fulfill({
      status: spec.status || 200,
      contentType: spec.contentType || "application/json",
      body: spec.raw !== undefined ? spec.raw : JSON.stringify(spec.json),
    });
  });
}

// Serves the real dashboard with a handling marking filled in, so the export
// path can be exercised without inventing production wording.
async function withMarking(page, marking = TEST_MARKING) {
  await page.route("**/dashboard", async (route) => {
    const response = await route.fetch();
    const html = await response.text();
    const escaped = marking.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
    const patched = html.replace(
      '<meta name="phm-handling-marking" content="">',
      `<meta name="phm-handling-marking" content="${escaped}">`,
    );
    if (patched === html) {
      throw new Error("handling-marking meta tag not found in /dashboard");
    }
    await route.fulfill({ response, body: patched });
  });
}

async function openDashboard(page) {
  await page.goto("/dashboard");
}

async function waitForShortlist(page) {
  await page.locator("#review-type:not([disabled])").waitFor();
}

// Minimal RFC 4180 reader for asserting exported files.
function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i += 1; }
      else if (c === '"') { quoted = false; }
      else { cell += c; }
    } else if (c === '"') {
      quoted = true;
    } else if (c === ",") {
      row.push(cell); cell = "";
    } else if (c === "\r" && text[i + 1] === "\n") {
      row.push(cell); rows.push(row); row = []; cell = ""; i += 1;
    } else {
      cell += c;
    }
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  return rows;
}

module.exports = {
  TEST_MARKING,
  MIXED_FLEET,
  CLEAN_FLEET,
  subsystem,
  platform,
  largeFleet,
  mockPlatforms,
  withMarking,
  openDashboard,
  waitForShortlist,
  parseCsv,
};
