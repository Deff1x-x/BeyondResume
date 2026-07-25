/**
 * Browser smoke: Career Companion Generate plan (target_role).
 * Run: node scripts/runtime-companion-smoke.mjs
 */
import { chromium } from "playwright";

const FRONTEND = process.env.FRONTEND_URL || "http://127.0.0.1:3000";
const API = process.env.API_URL || "http://127.0.0.1:8000/api/v1";

async function registerAndLogin() {
  const email = `runtime.ui.${Date.now()}@example.com`;
  const password = "RuntimeTest123!";
  const reg = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      password_confirmation: password,
      role: "candidate",
      terms_accepted: true,
      privacy_accepted: true
    })
  });
  if (!reg.ok) throw new Error(`register failed ${reg.status} ${await reg.text()}`);
  const login = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!login.ok) throw new Error(`login failed ${login.status} ${await login.text()}`);
  const { access_token } = await login.json();
  await fetch(`${API}/candidate/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access_token}`
    },
    body: JSON.stringify({ target_role: "Backend Developer" })
  });
  return { access_token };
}

async function main() {
  const { access_token } = await registerAndLogin();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const companionErrors = [];
  const generateResponses = [];

  page.on("console", (msg) => {
    if (msg.type() === "error" && !msg.text().includes("404 (Not Found)")) {
      companionErrors.push(msg.text());
    }
  });

  page.on("response", async (res) => {
    if (res.url().includes("/candidate/career-companion/generate") && res.request().method() === "POST") {
      generateResponses.push({
        status: res.status(),
        url: res.url(),
        method: res.request().method(),
        requestBody: res.request().postData(),
        bodyPreview: (await res.text()).slice(0, 400)
      });
    }
  });

  await page.goto(`${FRONTEND}/`, { waitUntil: "domcontentloaded" });
  await page.evaluate((token) => {
    sessionStorage.setItem("beyondresume_access_token", token);
  }, access_token);
  await page.goto(`${FRONTEND}/`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: /Your evidence-guided growth plan/i }).waitFor({
    timeout: 30000
  });

  await page.locator("#companion-role").fill("Backend Developer");
  await page.getByRole("button", { name: /Generate plan/i }).click();
  await page.getByRole("heading", { name: "Fix Now", exact: true }).waitFor({ timeout: 120000 });

  const hasBuildNext = (await page.getByRole("heading", { name: "Build Next", exact: true }).count()) > 0;
  const genModeText = await page.locator("text=/Generated via/i").first().textContent();
  const requestFailedVisible = await page.getByText("Request failed").count();

  await page.reload({ waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Fix Now", exact: true }).waitFor({ timeout: 30000 });

  await page.getByRole("button", { name: /Regenerate plan|Generate plan/i }).click();
  await page.getByRole("heading", { name: "Fix Now", exact: true }).waitFor({ timeout: 120000 });

  // Active plan uniqueness for this candidate
  const plan = await fetch(`${API}/candidate/career-companion`, {
    headers: { Authorization: `Bearer ${access_token}` }
  }).then((r) => r.json());

  const report = {
    ok: true,
    hasBuildNext,
    genModeText,
    requestFailedVisible,
    generateResponses,
    planId: plan.id,
    generationMode: plan.generation_mode,
    actionHorizons: [...new Set((plan.actions || []).map((a) => a.horizon))],
    companionErrors
  };
  console.log(JSON.stringify(report, null, 2));

  await browser.close();

  const allGenerateOk = generateResponses.every((r) => r.status === 200);
  if (!allGenerateOk || requestFailedVisible > 0 || !hasBuildNext) {
    process.exit(2);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
