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
    throw new Error(`register failed ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

const stamp = Date.now();
const employerAuth = await registerViaApi(
  `employer.polish2.${stamp}@example.com`,
  "Password123!",
  "employer"
);
const candidateAuth = await registerViaApi(
  `candidate.polish2.${stamp}@example.com`,
  "Password123!",
  "candidate"
);

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
    description: "Demo company for UI polish"
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
const vacancy = await vacancyRes.json();
console.log("vacancy", vacancyRes.status, vacancy?.id);

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });

const employerPage = await context.newPage();
await employerPage.addInitScript((token) => {
  sessionStorage.setItem("beyondresume_access_token", token);
}, employerAuth.access_token);
await employerPage.goto(`${BASE}/`, { waitUntil: "networkidle" });
await employerPage.waitForTimeout(1600);
await employerPage.screenshot({ path: path.join(OUT, "employer.png"), fullPage: true });
console.log("employer");

if (vacancy?.id) {
  await employerPage.goto(
    `${BASE}/employer/vacancies/${vacancy.id}/compare?ids=demo-a,demo-b`,
    { waitUntil: "networkidle" }
  );
  await employerPage.waitForTimeout(1000);
  await employerPage.screenshot({ path: path.join(OUT, "ai-compare.png"), fullPage: true });
  console.log("ai-compare");
}

const candidatePage = await context.newPage();
await candidatePage.addInitScript((token) => {
  sessionStorage.setItem("beyondresume_access_token", token);
}, candidateAuth.access_token);
await candidatePage.goto(`${BASE}/`, { waitUntil: "networkidle" });
await candidatePage.waitForTimeout(1600);
await candidatePage.screenshot({ path: path.join(OUT, "candidate.png"), fullPage: true });
console.log("candidate");

await browser.close();
