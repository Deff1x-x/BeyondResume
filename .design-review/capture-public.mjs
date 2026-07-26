import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.BASE_URL || "http://localhost:3002";
const API = process.env.API_URL || "http://127.0.0.1:8000/api/v1";
const OUT = path.resolve(__dirname);

async function registerViaApi(email, password, role) {
  const response = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      password_confirmation: password,
      role,
      terms_accepted: true,
      privacy_accepted: true
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`register failed ${response.status}: ${text}`);
  }
  return response.json();
}

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

await page.goto(`${BASE}/landing`, { waitUntil: "networkidle" });
await page.waitForTimeout(700);
await page.screenshot({ path: path.join(OUT, "landing.png"), fullPage: true });
console.log("landing");

await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
await page.locator("#email").fill("employer.demo@beyondresume.local");
await page.locator("#password").fill("Password123!");
await page.waitForTimeout(250);
await page.screenshot({ path: path.join(OUT, "login.png"), fullPage: true });
console.log("login");

await page.goto(`${BASE}/register`, { waitUntil: "networkidle" });
await page.locator('input[name="role"][value="candidate"]').check({ force: true });
await page.locator("#email").fill("candidate.demo@beyondresume.local");
await page.locator("#password").fill("Password123!");
const confirm = page.locator("#password_confirmation, #confirm_password, input[name='password_confirmation']");
if (await confirm.count()) {
  await confirm.first().fill("Password123!");
} else {
  const passwordInputs = page.locator('input[type="password"]');
  await passwordInputs.nth(1).fill("Password123!");
}
for (const box of await page.getByRole("checkbox").all()) {
  await box.check();
}
await page.waitForTimeout(250);
await page.screenshot({ path: path.join(OUT, "register.png"), fullPage: true });
console.log("register");

const stamp = Date.now();
const employerAuth = await registerViaApi(
  `employer.polish.${stamp}@example.com`,
  "Password123!",
  "employer"
);
const candidateAuth = await registerViaApi(
  `candidate.polish.${stamp}@example.com`,
  "Password123!",
  "candidate"
);

const employerPage = await context.newPage();
await employerPage.addInitScript((token) => {
  sessionStorage.setItem("beyondresume_access_token", token);
}, employerAuth.access_token);
await employerPage.goto(`${BASE}/`, { waitUntil: "networkidle" });
await employerPage.waitForTimeout(1500);
await employerPage.screenshot({ path: path.join(OUT, "employer.png"), fullPage: true });
console.log("employer");

const candidatePage = await context.newPage();
await candidatePage.addInitScript((token) => {
  sessionStorage.setItem("beyondresume_access_token", token);
}, candidateAuth.access_token);
await candidatePage.goto(`${BASE}/`, { waitUntil: "networkidle" });
await candidatePage.waitForTimeout(1500);
await candidatePage.screenshot({ path: path.join(OUT, "candidate.png"), fullPage: true });
console.log("candidate");

try {
  const headers = {
    Authorization: `Bearer ${employerAuth.access_token}`,
    "Content-Type": "application/json"
  };
  await fetch(`${API}/employer/company`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      company_name: "Polish Demo Co",
      website: "https://example.com",
      description: "Demo company"
    })
  });
  const vacancyRes = await fetch(`${API}/employer/vacancies`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      title: "Senior Frontend Engineer",
      description: "Evidence-backed hiring demo vacancy",
      status: "open"
    })
  });
  const vacancy = vacancyRes.ok ? await vacancyRes.json() : null;
  console.log("vacancy", vacancyRes.status, vacancy?.id);
  if (vacancy?.id) {
    await employerPage.goto(
      `${BASE}/employer/vacancies/${vacancy.id}/compare?ids=demo-a,demo-b`,
      { waitUntil: "networkidle" }
    );
    await employerPage.waitForTimeout(1200);
    await employerPage.screenshot({ path: path.join(OUT, "ai-compare.png"), fullPage: true });
    console.log("ai-compare");
  }
} catch (error) {
  console.log("ai-compare skipped:", error.message);
}

await browser.close();
