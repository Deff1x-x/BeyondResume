# HACKATHON MVP TECHNICAL SPECIFICATION v2.0 — Evidence-Based Hiring for Junior IT Specialists

## Основание документа и границы продукта

Титульная часть.
Статус документа: Approved for Hackathon Implementation.
Версия: v2.0.
Назначение: единственный источник требований для команды разработки и AI-ассистентов Codex/Cursor.
Режим реализации: 5 календарных дней, команда 2–4 человека, обязательный результат — стабильный end-to-end demo через UI.
Исходный документ v1.0 уже определял продукт как единое ТЗ для frontend, backend, AI, БД и deployment, при этом целился в полноценный MVP, пригодный не только для демонстрации, но и для пилота и дальнейшего развития. Именно эту исходную широту v2.0 сознательно сокращает до хакатонного масштаба. fileciteturn0file0L5-L17 fileciteturn0file0L22-L27

Статус и назначение документа.
Этот документ не является продуктовой концепцией и не является “roadmap note”. Это спецификация реализации. Если поведение не описано здесь, разработка его не добавляет. Такой же принцип был зафиксирован и в v1.0: документ должен быть единственным источником требований, а недоопределенное поведение не должно придумываться в коде. fileciteturn0file0L22-L27

Продуктовая проблема.
Для Junior IT-специалиста обычное резюме плохо доказывает способность выполнять рабочие задачи. Кандидат не понимает, на какие вакансии он реально подходит, какие навыки уже подтверждены, какие навыки “только заявлены”, и что именно нужно сделать, чтобы перейти из статуса “not ready” в “interviewable”. В исходном документе эта проблема была сформулирована через Skill Passport, Match Score, assessment и roadmap, а главным пользователем уже был указан Junior IT-специалист. fileciteturn0file0L14-L17 fileciteturn0file0L29-L38

Целевая аудитория.
Основной пользователь: выпускник, студент последнего курса, trainee/junior developer, в рамках MVP — прежде всего Junior Python Backend Developer.
Вторичный пользователь: работодатель/HR, которому нужен минимальный, объяснимый и немагический способ увидеть, почему кандидат находится выше или ниже в списке.
v1.0 уже фиксировал те же две роли и запрещал работодателю видеть людей вне своего контекста вакансии. v2.0 сохраняет это ограничение, но еще сильнее урезает employer-side scope. fileciteturn0file0L77-L97

Ценностное предложение.
Продукт дает не “AI verdict”, а evidence-based profile:
кандидат загружает резюме, добавляет один публичный репозиторий, получает структурированный Skill Passport, затем сопоставляет его с вакансией и видит не только общий балл, но и подтвержденные навыки, дефициты, уверенность оценки и следующий практический шаг. Это полностью согласуется с базовым принципом v1.0: оценка по подтвержденным доказательствам, а не только по словам резюме; финальное решение о найме остается за человеком. fileciteturn0file0L14-L17 fileciteturn0file0L40-L42

Основная гипотеза.
Если показать junior-кандидату и работодателю единый объяснимый слой “claim → evidence → deterministic score → gap → next action”, то:

кандидат точнее понимает, на какие вакансии подаваться сейчас;

работодатель быстрее видит, у кого есть реальные признаки готовности к junior-роль;

demo выглядит как инженерный AI-продукт, а не как чат-бот над резюме.

Scope freeze.
После конца Day 1, 18:00 local time список MUST HAVE замораживается. Новая функция может войти в scope только если из MUST HAVE удаляется функция сопоставимой сложности. Это обязательное правило процесса, а не рекомендация.

MUST HAVE, SHOULD HAVE, POST-MVP.

Это сокращение намеренно контрастирует с v1.0, где в MVP были включены аудит, версия AI-результатов, object storage, worker queue, admin-доступ и более широкий deployment stack. Для хакатона эти элементы выходят из MUST scope. fileciteturn0file0L44-L68 fileciteturn0file0L192-L210 fileciteturn0file0L881-L911

Главный принцип реализации.
LLM никогда не вычисляет финальный Match Score. Это правило уже было зафиксировано в v1.0 и в v2.0 остается абсолютным: LLM извлекает структуру, классифицирует evidence, пишет объяснение и rubric review в заданных пределах; все финальные числа считает backend. fileciteturn0file0L171-L175 fileciteturn0file0L342-L345 fileciteturn0file0L1059-L1070

## Пользовательские потоки и обязательные требования

Основной пользовательский сценарий.
Единственный сценарий, ради которого существует MVP:

Candidate регистрируется.

Заполняет краткий профиль.

Загружает резюме.

Добавляет один публичный GitHub repository.

Нажимает “Analyze profile”.

Система формирует Skill Passport.

Candidate открывает одну вакансию Junior Python Backend Developer.

Получает Match Score и breakdown.

Видит critical gaps и рекомендацию.

Получает одно практическое задание.

Отправляет решение в виде GitHub repo URL и короткого explanation.

Система делает deterministic checks + rubric-based AI review.

Score обновляется.

Кандидат видит roadmap 3–5 шагов.

Employer открывает вакансию, видит рейтинг, карточку кандидата и отправляет приглашение.

Этот путь полностью наследует core flow из v1.0, но убирает все, что не влияет на demo. fileciteturn0file0L111-L132 fileciteturn0file0L136-L147

Candidate user flow.

Employer user flow.

User stories.

Candidate-side MUST stories:

Как candidate, я хочу загрузить резюме и репозиторий, чтобы получить доказательный профиль.

Как candidate, я хочу увидеть общий match и его breakdown, чтобы понять, стоит ли подаваться.

Как candidate, я хочу получить одно короткое задание, чтобы доказать навыки делом.

Как candidate, я хочу увидеть score “до” и “после” assessment, чтобы понимать прирост.

Как candidate, я хочу получить roadmap из конкретных шагов, а не абстрактные советы.

Employer-side MUST stories:

Как employer, я хочу создать одну junior-вакансию с подтвержденными требованиями.

Как employer, я хочу видеть кандидатов отсортированными по объяснимому score.

Как employer, я хочу открыть карточку конкретного кандидата и увидеть, из чего сложился результат.

Как employer, я хочу отправить приглашение из системы.

Acceptance criteria.

Новый candidate может пройти регистрацию и логин.

Candidate может загрузить валидный PDF/DOCX и сохранить один GitHub URL.

После анализа система сохраняет не менее трех нормализованных skills, каждый с candidate_skill_score, confidence, evidence_strength.

Vacancy нельзя опубликовать без хотя бы одного required требования.

Match Score и все factor scores считаются только backend-ом.

На UI отображаются общий score, factor breakdown, critical gaps, evidence sources и confidence.

Candidate может получить assessment, отправить решение и увидеть обновленный match.

Employer видит ranking только внутри собственной вакансии.

Demo mode работает без внешнего LLM API.

Проект поднимается одной командой docker compose up. Docker Compose предназначен именно для определения и запуска multi-container приложений и поддерживает запуск стека одной командой docker compose up. [1]

Ключевые бизнес-правила.
Запрещено рассчитывать итоговый match в LLM, запрещено исполнять пользовательский код, запрещено использовать защищенные характеристики, запрещено показывать employer кандидатов вне контекста его вакансии, отсутствие данных уменьшает confidence, но само по себе не является доказательством “низкой способности”. Эти ограничения уже были явно сформулированы в v1.0 и в v2.0 наследуются без ослабления. fileciteturn0file0L483-L489 fileciteturn0file0L793-L796 fileciteturn0file0L825-L834 fileciteturn0file0L1059-L1070

## Архитектура, данные и API

Архитектурные принципы.
v2.0 — это modular monolith, а не сеть сервисов. Исходный документ уже допускал монолит и прямо говорил, что микросервисы для MVP не требуются; v2.0 делает это обязательным решением. fileciteturn0file0L231-L240

Выбранный стек.
Frontend: Next.js App Router + TypeScript + Tailwind CSS. App Router является актуальным маршрутизатором Next.js и использует Server Components, Suspense и современные возможности React; create-next-app по умолчанию поднимает TypeScript, Tailwind и App Router, что уменьшает bootstrap time для хакатона. [2]
Backend: FastAPI + Python 3.12.
Validation: Pydantic v2. Pydantic v2 сместил базовую API-модель к model_validate, а конфигурация from_attributes и strict-настройки позволяют делать жесткую валидацию структурированного AI output. [3]
Database: PostgreSQL 16.
ORM/Migrations: SQLAlchemy 2 + Alembic. SQLAlchemy 2 дает полноценный ORM и 2.0-style querying; Alembic является штатным lightweight migration tool для SQLAlchemy и поддерживает autogenerate и alembic check для CI. [4]
Deployment: Docker Compose.

Почему без Redis/Celery.
FastAPI официально поддерживает BackgroundTasks для операций, которые должны стартовать после ответа клиенту, включая обработку файлов; сами docs отдельно отмечают, что Celery и внешняя очередь нужны скорее для тяжелых distributed jobs, тогда как для небольших background tasks внутри того же приложения достаточно BackgroundTasks. Для одноузлового хакатонного MVP это более простой и надежный выбор, чем Redis/Celery. [5]

Итоговое решение по job processing.

Без Redis

Без Celery

Без отдельного worker container

Используется таблица jobs в PostgreSQL

Исполнение через FastAPI BackgroundTasks

Frontend получает статус через polling

Общая архитектура.

Next.js Web App
   |
   v
FastAPI REST API
   |
   +-- Auth Module
   +-- Candidate Module
   +-- Vacancy Module
   +-- Matching Module
   +-- Assessment Module
   +-- Roadmap Module
   +-- AI Orchestrator
   |
   +-- PostgreSQL
   +-- Local uploads volume (/app/data/uploads)

Структура репозитория.

/
  frontend/
    app/
    components/
    features/
    lib/
    styles/
    tests/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      integrations/
      prompts/
      utils/
    tests/
    alembic/
  fixtures/
    ai/
    resumes/
    repos/
  infra/
    docker/
  docs/
    SPECIFICATION.md
  docker-compose.yml
  .env.example
  README.md

Frontend architecture.

Next.js App Router

app/ routes

Server-rendered shell + client components for forms and polling

TanStack Query for fetching and polling

Zod for client-side validation

No business formulas in frontend

No direct AI calls from browser

Backend architecture.

api layer — routers and auth dependencies

schemas — request/response Pydantic models

services — business logic

models — SQLAlchemy ORM

integrations/llm.py — single LLM adapter

prompts/ — versioned prompt templates stored as plaintext files

utils/github_scan.py — deterministic repository scanner

utils/resume_parse.py — PDF/DOCX text extraction

AI architecture.

Один AIOrchestrator

Один provider interface

Пять prompt families:

resume_extraction_v1

vacancy_parse_v1

repo_evidence_v1

match_explainer_v1

roadmap_generator_v1

Шестой prompt опционален:

assessment_review_v1

Job processing и polling.
Только следующие операции работают как async jobs:

profile analysis

assessment review

roadmap generation
Vacancy parse — синхронный.
Match calculation — синхронный deterministic calculation + короткий synchronous AI explanation, потому что для demo нужен единый экран результата сразу.

Polling contract:

первые 30 секунд: GET /api/v1/jobs/{job_id} каждые 3 секунды

затем: каждые 5 секунд

stop on succeeded|failed

Job states:

queued

running

succeeded

failed

Resume processing.
Загрузка файлов в FastAPI через UploadFile подходит для form-based file upload; docs отдельно отмечают его преимущества для file-like обработки и spooled temp storage. В MVP используется именно этот механизм. [6]

Resume pipeline: 1. Validate MIME and extension. 2. Save original file locally. 3. Extract text:

PDF → pypdf

DOCX → python-docx or docx2txt

Normalize whitespace.

Remove obvious PII from AI payload:

email

phone

street address

exact birth date

Send extracted text to resume_extraction_v1.

Persist raw AI JSON.

Build or update current Skill Passport.

Limits:

Allowed MIME: application/pdf, DOCX office MIME

Max file size: 8 MiB

Max extracted text sent to LLM: 40,000 characters

Parse timeout: 20 seconds

Vacancy processing.
Vacancy creation в MUST scope выполняется через структурированную форму. Текстовый AI parse — SHOULD HAVE. Если включен: 1. Employer inserts raw vacancy text. 2. Backend calls vacancy_parse_v1. 3. Response is shown as editable requirements form. 4. Vacancy cannot be published until employer confirms parsed requirements.
Это соответствует исходному правилу v1.0: вакансия не публикуется без подтверждения требований работодателем. fileciteturn0file0L1065-L1067

GitHub repository processing.
v2.0 жестко запрещает анализировать весь GitHub-профиль. Разрешен только один публичный repository URL.

Deterministic repo scan constraints:

URL pattern: https://github.com/{owner}/{repo} only

Clone command: git clone --depth 1 --single-branch --no-tags

Clone timeout: 30 s

Repo total size after clone: ≤ 15 MiB

Traversal depth: ≤ 6

Scanned text files: ≤ 60

Single scanned file size: ≤ 40 KiB

Total text context passed to LLM: ≤ 100 KiB

Binary files: ignored

Symlinks: ignored

Hidden git data: ignored

User code execution: forbidden

Excluded directories:

.git

node_modules

venv

.venv

__pycache__

dist

build

.next

.turbo

coverage

target

vendor

.idea

.vscode

Excluded filenames/patterns:

package-lock.json

poetry.lock

Pipfile.lock

yarn.lock

pnpm-lock.yaml

*.min.js

*.png, *.jpg, *.jpeg, *.gif, *.mp4, *.mov, *.pdf

any file with NUL byte in first 8 KiB

Allowed text extensions:

.py

.md

.txt

.toml

.yaml

.yml

.json

.sql

.ini

.cfg

.env.example

Dockerfile

docker-compose.yml

Selection strategy before LLM: 1. Always include root README.md if exists. 2. Always include dependency file: pyproject.toml, requirements.txt, or Pipfile. 3. Prefer backend source under app/, src/, api/. 4. Prefer tests under tests/. 5. Include Dockerfile, docker-compose.yml, alembic.ini, migration files if present. 6. Rank remaining files by:

backend relevance

recency in git tree not used in MVP

filename heuristics

import density and function/class presence

Secret detection:

regex scan for obvious tokens/keys

if suspected secret appears, file is excluded from LLM payload and warning is stored

Assessment processing.
Assessment в v2.0 не генерируется “на лету” произвольным AI. Для надежности используется один фиксированный template под роль Junior Python Backend Developer.

Task template:

Build a small FastAPI service for task management

Requirements:

CRUD for tasks

PostgreSQL integration

basic validation

README

tests

Optional bonus:

Dockerfile

migration

error handling polish

Estimated time: 3–4 hours.

Submission:

one public GitHub repository URL

one text explanation 300–2000 chars

Evaluation split:

deterministic checks by code

rubric-based review by AI

Deterministic checks:

README exists

tests directory exists

Dockerfile exists

app/source directory exists

requirements or pyproject exists

basic API files exist

migration files present

.gitignore exists

probable secret not detected

error handling markers present in codebase

docs/openapi examples optional

AI review checks:

code structure readability

claim-evidence consistency

whether README explains setup and architecture

whether test strategy matches actual repo

whether explanation text demonstrates understanding

Combination rule:

deterministic score = 60% of final assessment score

AI rubric score = 40% of final assessment score

if AI response invalid → use deterministic score only and mark confidence low

Skill Passport.
Skill Passport in v2.0 — это текущий срез, а не историческая библиотека версий.

Passport contains:

normalized skill name

category

raw skill score

candidate skill score

evidence strength

confidence

evidence tier

evidence list

last evaluated at

Update rule:

profile analysis builds initial passport

assessment replaces only affected skill items and recomputes related scores

previous full history in UI is not shown

raw AI JSON remains stored for explainability

Matching Engine.
Matching is a backend-only service: 1. Load current Skill Passport 2. Load vacancy requirements 3. Compute factor scores 4. Apply critical penalties and hard caps 5. Persist match row 6. Send fixed numeric factors to match_explainer_v1 7. Store explanation separately from arithmetic scores

Gap Analysis.

matched: requirement_score ≥ 0.85

partial: 0.50 ≤ requirement_score < 0.85

missing: requirement_score < 0.50

critical_missing: missing and is_critical=true

Roadmap generation. 1. Take current latest match 2. Select top 3–5 gaps by severity and learning leverage 3. Call roadmap_generator_v1 4. Validate output 5. Save roadmap

Модель данных.
Ниже приведена минимальная схема БД, достаточная для MUST scope.

Таблицы, поля, связи, constraints и индексы.

users

id UUID PK

email CITEXT UNIQUE NOT NULL

password_hash TEXT NOT NULL

role VARCHAR(20) CHECK role IN ('candidate','employer')

status VARCHAR(20) CHECK status IN ('active','blocked','deleted') DEFAULT 'active'

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

Indexes:

ux_users_email

ix_users_role

candidate_profiles

id UUID PK

user_id UUID UNIQUE FK users(id)

full_name VARCHAR(150) NOT NULL

headline VARCHAR(160)

country VARCHAR(80)

timezone VARCHAR(60)

desired_role VARCHAR(80) NOT NULL DEFAULT 'junior_python_backend_developer'

work_format VARCHAR(20) CHECK work_format IN ('remote','hybrid','onsite','any')

bio TEXT

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

employer_profiles

id UUID PK

user_id UUID UNIQUE FK users(id)

company_name VARCHAR(160) NOT NULL

website VARCHAR(255)

description TEXT

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

resumes

id UUID PK

candidate_id UUID FK candidate_profiles(id)

original_filename VARCHAR(255) NOT NULL

stored_path TEXT NOT NULL

mime_type VARCHAR(100) NOT NULL

file_size_bytes INTEGER NOT NULL

extracted_text TEXT

parse_status VARCHAR(20) CHECK parse_status IN ('uploaded','parsed','failed')

created_at TIMESTAMPTZ

Index:

ix_resumes_candidate_created(candidate_id, created_at desc)

candidate_projects

id UUID PK

candidate_id UUID FK candidate_profiles(id)

title VARCHAR(160) NOT NULL

description TEXT NOT NULL

project_url VARCHAR(255)

github_url VARCHAR(255)

technologies JSONB DEFAULT '[]'

role_in_project VARCHAR(120)

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

vacancies

id UUID PK

employer_id UUID FK employer_profiles(id)

title VARCHAR(160) NOT NULL

description TEXT

role VARCHAR(80) NOT NULL DEFAULT 'junior_python_backend_developer'

seniority VARCHAR(20) NOT NULL DEFAULT 'junior'

work_format VARCHAR(20) CHECK work_format IN ('remote','hybrid','onsite')

location VARCHAR(120)

mentoring_available BOOLEAN DEFAULT TRUE

status VARCHAR(20) CHECK status IN ('draft','published','closed') DEFAULT 'draft'

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

vacancy_requirements

id UUID PK

vacancy_id UUID FK vacancies(id)

normalized_skill VARCHAR(80) NOT NULL

display_name VARCHAR(80) NOT NULL

requirement_type VARCHAR(20) CHECK requirement_type IN ('required','desired')

importance SMALLINT CHECK importance BETWEEN 1 AND 5

minimum_score SMALLINT CHECK minimum_score BETWEEN 0 AND 100

evidence_required BOOLEAN DEFAULT TRUE

is_critical BOOLEAN DEFAULT FALSE

Unique:

(vacancy_id, normalized_skill, requirement_type)

jobs

id UUID PK

user_id UUID FK users(id)

job_type VARCHAR(40) CHECK job_type IN ('profile_analysis','assessment_review','roadmap_generation')

entity_type VARCHAR(40)

entity_id UUID

status VARCHAR(20) CHECK status IN ('queued','running','succeeded','failed')

error_code VARCHAR(80)

error_message TEXT

result_ref_type VARCHAR(40)

result_ref_id UUID

created_at TIMESTAMPTZ

started_at TIMESTAMPTZ

finished_at TIMESTAMPTZ

ai_runs

id UUID PK

job_id UUID NULL FK jobs(id)

prompt_name VARCHAR(80) NOT NULL

prompt_version VARCHAR(20) NOT NULL

provider VARCHAR(40) NOT NULL

model VARCHAR(80) NOT NULL

input_hash VARCHAR(64) NOT NULL

request_json JSONB NOT NULL

response_json JSONB

validation_status VARCHAR(20) CHECK validation_status IN ('valid','invalid','fallback')

latency_ms INTEGER

created_at TIMESTAMPTZ

Index:

ix_ai_runs_input_hash

skill_passports

id UUID PK

candidate_id UUID UNIQUE FK candidate_profiles(id)

source_status VARCHAR(20) CHECK source_status IN ('empty','generated','updated')

resume_ai_run_id UUID NULL FK ai_runs(id)

repo_ai_run_id UUID NULL FK ai_runs(id)

raw_resume_json JSONB

raw_repo_json JSONB

generated_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

skill_passport_items

id UUID PK

passport_id UUID FK skill_passports(id)

normalized_skill VARCHAR(80) NOT NULL

display_name VARCHAR(80) NOT NULL

category VARCHAR(40)

raw_skill_score NUMERIC(5,2) CHECK raw_skill_score BETWEEN 0 AND 100

candidate_skill_score NUMERIC(5,2) CHECK candidate_skill_score BETWEEN 0 AND 100

confidence NUMERIC(4,3) CHECK confidence BETWEEN 0 AND 1

evidence_strength NUMERIC(4,3) CHECK evidence_strength BETWEEN 0 AND 1

evidence_tier VARCHAR(40) CHECK evidence_tier IN ('self_only','resume_only','resume_plus_project_text','repo_or_assessment')

source_clusters JSONB NOT NULL DEFAULT '[]'

last_evaluated_at TIMESTAMPTZ

Unique:

(passport_id, normalized_skill)

skill_evidence

id UUID PK

passport_item_id UUID FK skill_passport_items(id)

source_kind VARCHAR(30) CHECK source_kind IN ('resume','project_text','repo_code','assessment','candidate_text')

source_ref VARCHAR(120) NOT NULL

description TEXT NOT NULL

source_quality NUMERIC(4,3)

relevance NUMERIC(4,3)

recency NUMERIC(4,3)

extraction_confidence NUMERIC(4,3)

evidence_item_quality NUMERIC(4,3)

correlation_multiplier NUMERIC(4,3)

adjusted_quality NUMERIC(4,3)

matches

id UUID PK

candidate_id UUID FK candidate_profiles(id)

vacancy_id UUID FK vacancies(id)

initial_technical_score NUMERIC(5,2)

initial_evidence_score NUMERIC(5,2)

initial_level_fit NUMERIC(5,2)

initial_gap_recoverability NUMERIC(5,2)

initial_format_fit NUMERIC(5,2)

initial_critical_penalty NUMERIC(5,2)

initial_final_score NUMERIC(5,2)

updated_technical_score NUMERIC(5,2)

updated_evidence_score NUMERIC(5,2)

updated_level_fit NUMERIC(5,2)

updated_gap_recoverability NUMERIC(5,2)

updated_format_fit NUMERIC(5,2)

updated_critical_penalty NUMERIC(5,2)

updated_final_score NUMERIC(5,2)

initial_breakdown_json JSONB NOT NULL

updated_breakdown_json JSONB

explanation_json JSONB

current_stage VARCHAR(20) CHECK current_stage IN ('initial_only','updated') DEFAULT 'initial_only'

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

Unique:

(candidate_id, vacancy_id)

assessments

id UUID PK

candidate_id UUID FK candidate_profiles(id)

vacancy_id UUID FK vacancies(id)

title VARCHAR(160) NOT NULL

task_text TEXT NOT NULL

estimated_hours SMALLINT DEFAULT 4

status VARCHAR(20) CHECK status IN ('assigned','submitted','reviewed') DEFAULT 'assigned'

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

Unique:

(candidate_id, vacancy_id)

assessment_submissions

id UUID PK

assessment_id UUID UNIQUE FK assessments(id)

repo_url VARCHAR(255) NOT NULL

explanation TEXT NOT NULL

submitted_at TIMESTAMPTZ

assessment_results

id UUID PK

submission_id UUID UNIQUE FK assessment_submissions(id)

deterministic_score NUMERIC(5,2)

ai_rubric_score NUMERIC(5,2)

final_assessment_score NUMERIC(5,2)

confidence NUMERIC(4,3)

deterministic_json JSONB NOT NULL

ai_review_json JSONB

review_status VARCHAR(20) CHECK review_status IN ('deterministic_only','full_review')

created_at TIMESTAMPTZ

invitations

id UUID PK

employer_id UUID FK employer_profiles(id)

candidate_id UUID FK candidate_profiles(id)

vacancy_id UUID FK vacancies(id)

message TEXT

status VARCHAR(20) CHECK status IN ('sent','seen') DEFAULT 'sent'

created_at TIMESTAMPTZ

API endpoints.

Request/response schemas.

POST /api/v1/auth/register

{
  "email": "user@example.com",
  "password": "StrongPass123",
  "role": "candidate"
}

Response 201:

{
  "id": "uuid",
  "email": "user@example.com",
  "role": "candidate"
}

POST /api/v1/candidate/analyze

Request:

{}

Response 202:

{
  "job_id": "uuid",
  "status": "queued"
}

GET /api/v1/jobs/{job_id}

{
  "id": "uuid",
  "job_type": "profile_analysis",
  "status": "running",
  "error_code": null,
  "result_ref_type": null,
  "result_ref_id": null
}

POST /api/v1/vacancies/{id}/match

Response 200:

{
  "match_id": "uuid",
  "current_stage": "initial_only",
  "scores": {
    "technical": 82.12,
    "evidence": 65.24,
    "level_fit": 100.0,
    "gap_recoverability": 77.16,
    "format_fit": 100.0,
    "critical_penalty": 0.0,
    "final": 82.12
  },
  "category": "good_match",
  "critical_gaps": [],
  "matched_skills": ["python", "fastapi"],
  "partial_skills": ["postgresql"],
  "missing_skills": ["docker", "testing"],
  "explanation": {
    "candidate_summary": "…",
    "employer_summary": "…",
    "recommendation": "apply"
  }
}

POST /api/v1/assessments/{id}/submit

{
  "repo_url": "https://github.com/user/task-service",
  "explanation": "I used FastAPI, SQLAlchemy, Alembic and pytest..."
}

Response 202:

{
  "job_id": "uuid",
  "status": "queued"
}

GET /api/v1/employer/vacancies/{id}/candidates

{
  "vacancy_id": "uuid",
  "items": [
    {
      "candidate_id": "uuid",
      "full_name": "Aigerim Nur",
      "final_score": 89.2,
      "stage": "updated",
      "top_strengths": ["python", "fastapi"],
      "critical_gaps": []
    }
  ]
}

Error format.
v2.0 сохраняет единый envelope error format v1.0, потому что он уже достаточно прост и пригоден для frontend. fileciteturn0file0L697-L722

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": [
      {"field": "repo_url", "issue": "invalid_github_url"}
    ],
    "request_id": "uuid"
  }
}

## AI, схемы и детерминированный скоринг

Общие правила AI layer.
v1.0 уже требовал JSON-only output, prompt versioning, retries, запрет на protected characteristics и запрет для модели считать итоговый Match Score. v2.0 сохраняет все эти ограничения, но упрощает orchestration до одного adapter и набора prompt templates. fileciteturn0file0L475-L489 fileciteturn0file0L638-L653

AI JSON schemas.

resume_extraction_v1

{
  "target_role": "junior_python_backend_developer",
  "seniority": "junior",
  "skills": [
    {
      "name": "Python",
      "normalized_name": "python",
      "estimated_score": 72,
      "confidence": 0.81,
      "evidence": [
        {
          "source_type": "resume",
          "source_reference": "resume:latest",
          "description": "Built REST API with FastAPI for university project",
          "source_quality": 0.45,
          "relevance": 0.95,
          "recency": 0.80,
          "confidence": 0.84
        }
      ],
      "missing_information": []
    }
  ],
  "strengths": ["api development"],
  "limitations": ["little production evidence"],
  "warnings": []
}

vacancy_parse_v1 (SHOULD HAVE)

{
  "role": "junior_python_backend_developer",
  "seniority": "junior",
  "work_format": "remote",
  "mentoring_available": true,
  "requirements": [
    {
      "skill_name": "Python",
      "normalized_name": "python",
      "type": "required",
      "importance": 5,
      "minimum_score": 60,
      "evidence_required": true,
      "is_critical": true,
      "rationale": "Main implementation language"
    }
  ],
  "ambiguities": []
}

repo_evidence_v1

{
  "repository_summary": "Small FastAPI service with tests and Dockerfile",
  "skills": [
    {
      "normalized_name": "fastapi",
      "estimated_score": 76,
      "confidence": 0.83,
      "evidence": [
        {
          "source_type": "repo_code",
          "source_reference": "app/main.py",
          "description": "FastAPI app with routes and dependency injection",
          "source_quality": 0.85,
          "relevance": 0.97,
          "recency": 0.90,
          "confidence": 0.82
        }
      ]
    }
  ],
  "warnings": ["no runtime execution performed"]
}

match_explainer_v1

{
  "candidate_summary": "Strong in Python and API basics; moderate gap in testing.",
  "employer_summary": "Candidate is interviewable for junior backend with mentoring.",
  "matched_requirements": [
    {"skill": "python", "reason": "score above requirement with repo evidence"}
  ],
  "partial_requirements": [
    {"skill": "postgresql", "gap": "schema and migration depth is limited", "severity": "medium"}
  ],
  "missing_requirements": [
    {"skill": "testing", "severity": "medium"}
  ],
  "risks": ["evidence is mostly academic"],
  "recommendation": "apply",
  "disclaimer": "Score is advisory and not a hiring decision."
}

roadmap_generator_v1

{
  "steps": [
    {
      "order": 1,
      "skill": "testing",
      "title": "Add pytest coverage for service layer",
      "action": "Write tests for success and error cases of two endpoints.",
      "deliverable": "At least 8 passing tests in repository",
      "verification_method": "repository review",
      "estimated_hours": 4,
      "success_criteria": ["tests pass", "critical service flow covered"]
    }
  ],
  "total_estimated_hours": 16
}

assessment_review_v1 (optional but included in MUST because one-role scope makes it realistic)

{
  "criterion_scores": {
    "correctness": {"score": 16, "max": 20, "evidence": ["CRUD endpoints implemented"]},
    "code_quality": {"score": 14, "max": 20, "evidence": ["clear file separation"]},
    "architecture": {"score": 14, "max": 20, "evidence": ["service/repository structure"]},
    "testing": {"score": 8, "max": 15, "evidence": ["pytest folder exists with API tests"]},
    "error_handling": {"score": 7, "max": 10, "evidence": ["HTTPException used"]},
    "documentation": {"score": 8, "max": 10, "evidence": ["README with setup"]},
    "explanation": {"score": 4, "max": 5, "evidence": ["candidate explains trade-offs"]}
  },
  "total_score": 71,
  "confidence": 0.78,
  "skill_updates": [
    {"skill": "fastapi", "score": 78, "evidence_quality": 0.92, "reason": "working API with tests"}
  ],
  "critical_issues": [],
  "limitations": ["code was not executed"]
}

Prompt rules.

Модель возвращает только JSON.

Модель не добавляет навыки, если во входе нет evidence.

Модель не предполагает пол, возраст, национальность, здоровье, религию, семейное положение.

Модель не считает итоговый Match Score.

Модель при неопределенности заполняет warnings/limitations/missing_information.

Для assessment review каждый критерий обязан иметь evidence list.

Для roadmap каждый шаг обязан иметь measurable deliverable.

Validation, fallback, timeout, retry.

Validation: Pydantic response models

Retry policy: 1 retry on invalid JSON

Timeout per AI call: 20 seconds

On second failure:

profile analysis → fail job

match explanation → fallback deterministic text template

roadmap → fallback deterministic roadmap from gap templates

assessment review → deterministic-only review result

ai_runs.validation_status becomes fallback when fallback used

Mock mode.
v1.0 уже предусматривал LLM_PROVIDER=mock и offline demo mode с fixture JSON по input hash. v2.0 делает это обязательным MUST HAVE. fileciteturn0file0L997-L1006

Mock mode contract:

env: LLM_PROVIDER=mock

key: {prompt_name}:{sha256(payload)}

fixture path: fixtures/ai/{prompt_name}/{hash}.json

if exact hash not found → use nearest named fixture by scenario:

candidate_strong

candidate_partial

candidate_weak

Полные формулы скоринга.

Для evidence item i:

evidence_item_quality_i =
  clamp(
    0.35 * source_quality_i +
    0.25 * relevance_i +
    0.20 * recency_i +
    0.20 * extraction_confidence_i,
    0, 1
  )

Корреляционный множитель для дублирующих evidence в одном source cluster:

cluster examples: resume, project_text, repo_code, assessment, candidate_text

Если у evidence в этом кластере уже был k-й более сильный элемент раньше после сортировки по evidence_item_quality desc, то:

correlation_multiplier_i = 1 / (1 + 0.35 * previous_items_in_same_cluster)

Следовательно:

первый item in cluster → 1.00

второй → 0.74

третий → 0.59

четвертый → 0.49

adjusted_q_i = evidence_item_quality_i * correlation_multiplier_i

Evidence Strength навыка:

evidence_strength =
  1 - Π(1 - adjusted_q_i)

Raw skill score:

raw_skill_score =
  weighted_average(source_score_i, weight = adjusted_q_i)

Candidate Skill Score:

candidate_skill_score_base =
  raw_skill_score * (0.45 + 0.55 * evidence_strength)

Evidence tier caps:

self_only → max 40

resume_only → max 55

resume_plus_project_text → max 65

repo_or_assessment → max 100

candidate_skill_score =
  min(candidate_skill_score_base, evidence_tier_cap)

Confidence:

source_diversity =
  distinct_source_clusters / 4

confidence =
  clamp(
    0.55 * evidence_strength +
    0.25 * source_diversity +
    0.20 * min(distinct_evidence_items / 4, 1),
    0, 1
  )

Coverage of requirement r:

coverage_r =
  min(candidate_skill_score_r / required_minimum_score_r, 1.0)

If skill missing entirely:

coverage_r = 0
confidence flag = low

Evidence multiplier:

evidence_multiplier_r =
  1.0, if evidence_required = false
  0.60 + 0.40 * evidence_strength_r, if evidence_required = true

Requirement score:

requirement_score_r = coverage_r * evidence_multiplier_r

Technical score weights:

type_multiplier_r =
  1.00 for required
  0.45 for desired

weight_r = importance_r * type_multiplier_r

technical_score =
  100 * Σ(weight_r * requirement_score_r) / Σ(weight_r)

Evidence score:

evidence_score =
  100 * Σ(weight_r * evidence_strength_r) / Σ(weight_r)

Level fit:

same level → 100

candidate below by 1 → 70

candidate below by 2+ → 30

candidate above by 1 → 90

candidate above by 2+ → 75

Gap severity for each required skill:

gap_ratio_r =
  max(required_minimum_score_r - candidate_skill_score_r, 0) / required_minimum_score_r

Weighted inverse gap severity across required skills:

inverse_gap_severity =
  1 - weighted_average(gap_ratio_r, weight = importance_r)

Prerequisite coverage:

prerequisite_coverage =
  weighted_average(coverage_r for required skills, weight = importance_r)

Assessment performance:

assessment_performance =
  final_assessment_score / 100, if assessment exists
  0.50, otherwise

Mentoring availability:

mentoring_availability =
  1.0 if vacancy.mentoring_available else 0.0

Gap Recoverability Score:

gap_recoverability =
  100 * (
    0.40 * assessment_performance +
    0.30 * prerequisite_coverage +
    0.20 * inverse_gap_severity +
    0.10 * mentoring_availability
  )

Format fit:

exact match → 100

candidate allows vacancy format → 85

one side unspecified → 70

explicit mismatch → 30

Critical penalty:

define critical missing as is_critical=true and coverage_r < 0.50

define severely missing as is_critical=true and coverage_r < 0.25

critical_penalty =
  min(
    15 * count(critical_missing) +
    10 * count(severely_missing),
    35
  )

Base match:

base_match =
  0.55 * technical_score +
  0.20 * evidence_score +
  0.10 * level_fit +
  0.10 * gap_recoverability +
  0.05 * format_fit

Raw final score:

raw_final_match_score =
  clamp(base_match - critical_penalty, 0, 100)

Hard caps:

if exactly one critical skill missing → final_score <= 69

if two or more critical skills missing → final_score <= 54

final_match_score =
  apply_hard_caps(raw_final_match_score)

Categories:

85–100 → strong_match

70–84.99 → good_match

55–69.99 → partial_match

40–54.99 → weak_match

<40 → not_ready

Псевдокод формул.

def compute_evidence_quality(item):
    q = (
        0.35 * item.source_quality +
        0.25 * item.relevance +
        0.20 * item.recency +
        0.20 * item.extraction_confidence
    )
    return clamp(q, 0, 1)


def apply_correlation_penalty(sorted_items_in_cluster):
    adjusted = []
    for idx, item in enumerate(sorted_items_in_cluster):
        multiplier = 1 / (1 + 0.35 * idx)
        adjusted.append(item.quality * multiplier)
    return adjusted


def compute_evidence_strength(evidence_items):
    per_cluster = group_by_cluster(evidence_items)
    adjusted_qs = []
    for cluster_items in per_cluster.values():
        sorted_items = sort_desc(cluster_items, key="quality")
        adjusted_qs.extend(apply_correlation_penalty(sorted_items))
    product = 1.0
    for q in adjusted_qs:
        product *= (1 - q)
    return 1 - product


def compute_skill_score(observations, evidence_tier):
    if not observations:
        return 0, 0, 0
    raw = weighted_average(
        [o.source_score for o in observations],
        [o.adjusted_q for o in observations]
    )
    evidence_strength = compute_evidence_strength(observations)
    base = raw * (0.45 + 0.55 * evidence_strength)
    cap_by_tier = {
        "self_only": 40,
        "resume_only": 55,
        "resume_plus_project_text": 65,
        "repo_or_assessment": 100,
    }[evidence_tier]
    score = min(base, cap_by_tier)
    source_diversity = distinct_clusters(observations) / 4
    confidence = clamp(
        0.55 * evidence_strength +
        0.25 * source_diversity +
        0.20 * min(len(observations) / 4, 1),
        0, 1
    )
    return raw, score, confidence


def compute_match(passport, vacancy, assessment_result=None):
    factors = []
    for req in vacancy.requirements:
        skill = passport.get(req.normalized_skill)
        if not skill:
            coverage = 0.0
            evidence_strength = 0.0
            candidate_score = 0.0
        else:
            candidate_score = skill.candidate_skill_score
            evidence_strength = skill.evidence_strength
            coverage = min(candidate_score / req.minimum_score, 1.0)

        if req.evidence_required:
            evidence_multiplier = 0.60 + 0.40 * evidence_strength
        else:
            evidence_multiplier = 1.0

        requirement_score = coverage * evidence_multiplier
        type_multiplier = 1.0 if req.requirement_type == "required" else 0.45
        weight = req.importance * type_multiplier

        factors.append({
            "req": req,
            "candidate_score": candidate_score,
            "coverage": coverage,
            "evidence_strength": evidence_strength,
            "requirement_score": requirement_score,
            "weight": weight
        })

    technical_score = 100 * weighted_average(
        [f["requirement_score"] for f in factors],
        [f["weight"] for f in factors]
    )

    evidence_score = 100 * weighted_average(
        [f["evidence_strength"] for f in factors],
        [f["weight"] for f in factors]
    )

    level_fit = compute_level_fit(passport.candidate_level, vacancy.seniority)
    prerequisite_coverage = weighted_average_required_coverages(factors)
    inverse_gap_severity = 1 - weighted_average_required_gaps(factors)

    assessment_performance = (
        assessment_result.final_assessment_score / 100
        if assessment_result else 0.50
    )
    mentoring = 1.0 if vacancy.mentoring_available else 0.0

    gap_recoverability = 100 * (
        0.40 * assessment_performance +
        0.30 * prerequisite_coverage +
        0.20 * inverse_gap_severity +
        0.10 * mentoring
    )

    format_fit = compute_format_fit(passport.work_format, vacancy.work_format)

    critical_missing = count(
        f for f in factors
        if f["req"].is_critical and f["coverage"] < 0.50
    )
    severely_missing = count(
        f for f in factors
        if f["req"].is_critical and f["coverage"] < 0.25
    )

    critical_penalty = min(15 * critical_missing + 10 * severely_missing, 35)

    base_match = (
        0.55 * technical_score +
        0.20 * evidence_score +
        0.10 * level_fit +
        0.10 * gap_recoverability +
        0.05 * format_fit
    )

    final = clamp(base_match - critical_penalty, 0, 100)

    if critical_missing == 1:
        final = min(final, 69)
    elif critical_missing >= 2:
        final = min(final, 54)

    return round_scores(...)

Расчетные примеры.

Пример A: хороший initial match.
Вакансия: Python(60, critical, imp5), FastAPI(50, critical, imp4), PostgreSQL(50, imp4), Docker desired(40, imp2), Testing desired(40, imp2).
Кандидат:

Python score 68.56, evidence 0.78

FastAPI score 60.91, evidence 0.72

PostgreSQL score 45.15, evidence 0.55

Docker score 30.15, evidence 0.40

Testing score 32.13, evidence 0.35

Requirement scores:

Python: coverage 1.00 × 0.912 = 0.912

FastAPI: coverage 1.00 × 0.888 = 0.888

PostgreSQL: 0.903 × 0.82 = 0.740

Docker: 0.754

Testing: 0.803

Technical:

technical_score = 84.28

Evidence:

evidence_score = 65.24

Gap recoverability:

assessment_performance = 0.50
prerequisite_coverage = 0.97
inverse_gap_severity = 0.903
mentoring = 1.0

gap_recoverability =
100 * (0.40*0.50 + 0.30*0.97 + 0.20*0.903 + 0.10*1.0)
= 77.16

Final:

base_match =
0.55*84.28 + 0.20*65.24 + 0.10*100 + 0.10*77.16 + 0.05*100
= 82.12

critical_penalty = 0
final_match_score = 82.12
category = good_match

Пример B: один отсутствующий critical skill.
Кандидат:

Python 54.28, evidence 0.70

FastAPI 18.45, evidence 0.30

PostgreSQL 29.30, evidence 0.45

Docker 19.60, evidence 0.20

Testing 16.45, evidence 0.25

Technical:

technical_score = 51.95
evidence_score = 46.66
gap_recoverability = 62.07
level_fit = 100
format_fit = 100

FastAPI is critical and coverage < 0.50, so:

critical_missing = 1
severely_missing = 0
critical_penalty = 15

Final:

base_match =
0.55*51.95 + 0.20*46.66 + 0.10*100 + 0.10*62.07 + 0.05*100
= 59.11

raw_final = 59.11 - 15 = 44.11
hard_cap_for_one_critical_missing = 69
final_match_score = 44.11
category = weak_match

Пример C: после assessment кандидат становится strong match.
После assessment:

Python 63.51, evidence 0.88

FastAPI 66.92, evidence 0.92

PostgreSQL 45.93, evidence 0.70

Docker 19.60, evidence 0.20

Testing 59.64, evidence 0.85

Technical:

technical_score = 89.22
evidence_score = 79.90
assessment_performance = 0.82
prerequisite_coverage = 0.974
inverse_gap_severity = 0.975
gap_recoverability = 91.52

Final:

base_match =
0.55*89.22 + 0.20*79.90 + 0.10*100 + 0.10*91.52 + 0.05*100
= 89.20

critical_penalty = 0
final_match_score = 89.20
category = strong_match

Пример D: cap на слабой evidence base.
Если skill “Docker” extracted only from resume with raw score 80 and evidence_strength 0.20:

base = 80 * (0.45 + 0.55*0.20) = 80 * 0.56 = 44.8
tier = resume_only
cap = 55
final skill score = 44.8

Если raw score был бы 95:

base = 95 * 0.56 = 53.2
cap = 55
final = 53.2

Если raw score 120 not possible because validation caps source scores to 0..100.

## Интерфейс, безопасность, тестирование и deployment

Frontend pages.

Candidate routes:

/ — landing

/auth/register

/auth/login

/candidate/onboarding

/candidate/profile

/candidate/passport

/candidate/vacancies

/candidate/vacancies/[id]

/candidate/matches/[id]

/candidate/assessments/[id]

/candidate/roadmap/[matchId]

/candidate/invitations

Employer routes:

/employer/dashboard

/employer/vacancies/new

/employer/vacancies/[id]

/employer/vacancies/[id]/candidates

/employer/vacancies/[id]/candidates/[candidateId]

Это остается близко к исходному набору страниц v1.0, но employer panel intentionally slimmer. fileciteturn0file0L723-L759

Главный экран результата match.
Обязательные UI блоки:

Final Match Score

factor breakdown

current stage badge: initial / updated after assessment

confirmed skills

evidence source icons: resume / repo / assessment

confidence

critical gaps

recommendation

delta block: before assessment → after assessment

UI states.

empty

loading/skeleton

queued/running job

succeeded with data

failed with retry CTA

partial fallback (LLM unavailable, deterministic result shown)

forbidden/not found

Security.
v1.0 уже требовал password hashing, JWT, RBAC, MIME/size validation, private file access, PII minimization и запрет на code execution. v2.0 берет только тот minimum set, который реально завершить за 5 дней. fileciteturn0file0L775-L788

Security requirements:

password hashing: Argon2id

JWT access token:

TTL 15 min

refresh token: omitted in MUST scope to reduce complexity
Instead:

access token + re-login for demo

refresh tokens = SHOULD HAVE

backend RBAC for candidate/employer

resume file MIME + ext + size validation

repo URL validation

no code execution

no shell interpolation from user URLs

strip email, phone, address from AI payload where possible

employer cannot view candidate outside own vacancy

.env secrets never committed

response logs must not include full resume text

Testing.
Исходный v1.0 справедливо требовал unit, integration и хотя бы один E2E сценарий. v2.0 сохраняет это, но фокусируется только на must flows. fileciteturn0file0L835-L880

Test matrix:

Unit tests:

evidence quality formula

correlation multiplier

evidence strength aggregation

candidate skill score caps

technical score

critical penalty and hard caps

gap recoverability

RBAC guards

repo URL validator

GitHub file filtering

Pydantic AI schema validation

Integration tests:

register/login/me

candidate profile + resume upload

analyze profile job completion

create vacancy + publish

match calculation

assessment submission + result

roadmap generation

employer ranking + invitation

E2E:

one Playwright journey:

candidate registers

uploads fixture resume

adds fixture repo

analyzes profile

opens vacancy

gets match

submits assessment

sees updated match

employer opens ranking

opens candidate card

sends invitation

Quality gates:

backend service/scoring coverage ≥ 80%

zero failing migrations

ruff/black/mypy green

frontend typecheck green

one green Playwright happy path

demo fixtures validate against schemas

Seed data.
v1.0 already required one employer, one Junior Python Developer vacancy, three candidates, AI fixtures and one completed assessment. v2.0 keeps exactly that because it is optimal for the demo. fileciteturn0file0L996-L1006

Seed set:

employer:

hr@demo.local

vacancy:

Junior Python Backend Developer

candidates:

candidate_strong@demo.local

candidate_partial@demo.local

candidate_weak@demo.local

each candidate:

profile

resume fixture

project fixture

one completed assessment for candidate_partial, so score delta can be demonstrated immediately

Docker and deployment.
Compose remains the mandatory local deployment abstraction because it is built exactly for defining and running multi-container applications from one configuration, and docker compose up creates/starts the application stack. [1]

Mandatory Compose services:

frontend

backend

postgres

No MUST services:

redis

minio

nginx

worker

sentry

docker-compose.yml target:

services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres]
    volumes:
      - ./data/uploads:/app/data/uploads

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ebh
      POSTGRES_USER: ebh
      POSTGRES_PASSWORD: ebh
    ports: ["5432:5432"]

Переменные окружения.

APP_ENV=local
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

DATABASE_URL=postgresql+psycopg://ebh:ebh@postgres:5432/ebh

JWT_SECRET=change_me
JWT_ACCESS_TTL_MINUTES=15

UPLOAD_DIR=/app/data/uploads
MAX_RESUME_MB=8

LLM_PROVIDER=mock
LLM_API_KEY=
LLM_MODEL=gpt-5-mini
LLM_TIMEOUT_SECONDS=20

GITHUB_CLONE_TIMEOUT_SECONDS=30
GITHUB_MAX_REPO_MB=15
GITHUB_MAX_FILES=60
GITHUB_MAX_FILE_KB=40
GITHUB_MAX_CONTEXT_KB=100

## План реализации, demo и операционная дисциплина

План разработки на 5 дней.

Распределение задач между 2–4 участниками.

Для 2 человек:

Dev A: backend, DB, formulas, AI integration

Dev B: frontend, UI polling, Playwright, seeds

Для 3 человек:

Dev A: auth/profile/resume/backend core

Dev B: scoring/matching/assessment/AI

Dev C: frontend/employer flow/demo polish

Для 4 человек:

Dev A: platform/bootstrap/auth/DB

Dev B: candidate analysis + AI

Dev C: matching + assessment + roadmap

Dev D: frontend + e2e + demo assets

Порядок работы Codex и Cursor.

Cursor: reading spec, navigation, interactive code edits, fast refactors

Codex: narrow vertical slices with explicit DoD

human lead approves schema and contract changes before code generation

no agent can change formulas or public API without spec reference

Формат промптов для Codex.

Контекст:
- Реализуется раздел: <название раздела спецификации>
- Текущий этап: <Day X / module>
- Текущий контракт: <вставить schema/API/model>

Задача:
- Реализуй один vertical slice:
  <пример: POST /api/v1/candidate/analyze + jobs table + BackgroundTasks runner>

Ограничения:
- Не добавляй новые бизнес-правила.
- Не используй технологии вне спецификации.
- Не меняй публичные DTO без обновления всех мест использования.
- Не добавляй WebSocket, Redis, Celery, MinIO.
- Все формулы должны совпадать со спецификацией.
- Любое AI output валидируй Pydantic model.

Definition of Done:
- Код компилируется
- Есть Alembic migration при изменении БД
- Есть unit/integration tests
- OpenAPI updated
- В конце дай список измененных файлов

Code review checklist. 1. Есть ли прямая связь с этим документом. 2. Не добавлена ли неописанная бизнес-логика. 3. Не ушли ли вычисления в frontend. 4. Не считает ли LLM итоговые scores. 5. Есть ли Pydantic validation для AI output. 6. Есть ли tests на формулы. 7. Не добавлены ли лишние infra dependencies. 8. Нет ли code execution path. 9. Соблюден ли RBAC. 10. Нет ли утечки PII в LLM payload. 11. Есть ли migration при схеме БД. 12. Не сломан ли demo mode.

Definition of Done каждого этапа.

Этап считается завершенным только если:

endpoint работает локально,

UI связался с endpoint,

negative case обработан,

есть минимум один тест,

путь включен в demo или явно помечен SHOULD HAVE.

Definition of Done всего MVP.
MVP готов, если через пользовательский интерфейс проходит полный путь: candidate profile → analysis → vacancy match → assessment submit → updated match → employer ranking → invitation, все данные лежат в PostgreSQL, AI outputs валидируются, demo mode не зависит от внешнего LLM, запуск из чистого окружения выполняется через Docker Compose. Это сохраняет core DoD из v1.0, но в более узком scope. fileciteturn0file0L1071-L1075

Demo script на 3 минуты.

Минута первая:

Открыть landing.

Быстро зайти под candidate demo account.

Показать profile + uploaded resume + repo.

Открыть Skill Passport.

Подчеркнуть: “это не free-text CV parse, а skills with evidence and confidence”.

Минута вторая:

Открыть одну vacancy.

Нажать match.

Показать:

final score

factor breakdown

critical gaps

evidence sources

Сразу перейти в assessment.

Показать, что submission уже reviewed in demo mode.

Вернуться к updated match и показать delta “до/после”.

Минута третья:

Зайти под employer.

Открыть ranking.

Показать тех же 3 кандидатов с разным score.

Открыть карточку improved candidate.

Отправить invitation.

Финальная реплика: “LLM here structures and explains evidence; hiring score itself is deterministic and testable.”

Возможные вопросы жюри и технические ответы.

Почему вы не используете многоагентную архитектуру?
Потому что для 5-дневного hackathon MVP многоагентность повышает риск и не увеличивает demo value. Один orchestrator и JSON contracts дают тот же observable результат с меньшей вероятностью поломки.

Почему без Redis/Celery?
Потому что у нас одноузловой demo-friendly deployment. FastAPI сам поддерживает BackgroundTasks для простых post-response jobs, а сами docs рекомендуют Celery уже для действительно тяжелых distributed workloads. [7]

Почему Match Score честный?
Потому что формулы детерминированы, покрываются unit tests, а LLM не может менять итоговые числа. Такой принцип был и в v1.0. fileciteturn0file0L171-L175 fileciteturn0file0L342-L345

Почему вы не запускаете код assessment solution?
Из соображений безопасности и сроков. Мы анализируем структуру repo, наличие тестов, README, Dockerfile, migrations и rubric evidence, но не исполняем untrusted code. Это прямо соответствует запрету из v1.0. fileciteturn0file0L72-L73 fileciteturn0file0L780-L780

Что будет, если LLM недоступен?
Сработает mock mode или deterministic fallback. Match arithmetic и basic assessment deterministic checks все равно работают.

Разве scoring weights научно подтверждены?
Нет. Это явно продуктовая гипотеза. Мы не делаем вид, что это психометрическая система. Мы делаем инженерно объяснимую ранжирующую эвристику.

Риски и план сокращения scope.

Главные риски:

PDF/DOCX parsing issues

unstable external LLM

repo scanner edge cases

frontend polish swallowing backend time

assessment review taking too long

Сокращение scope по приоритету: 1. Перевести vacancy parse из SHOULD HAVE в disabled 2. Оставить только mock provider 3. Упростить roadmap generation до deterministic template 4. Урезать employer UI до ranking + detail only 5. Если совсем критично — оставить assessment review deterministic-only и показывать AI review как disabled in live mode

Post-MVP roadmap.

refresh tokens

true vacancy text parse as standard flow

richer evidence normalization

more roles beyond junior python backend

sandboxed code execution environment

history/version browsing

ATS integrations

multi-tenant SaaS mode

Бизнес-модель.

candidate-facing free onboarding and self-check

employer-facing paid team workspace later

pilot model:

free candidate acquisition

paid employer pilot per vacancy or per seat

longer-term positioning:

recruit-tech platform for junior hiring with evidence-backed profiles

Метрики пилота.

candidate profile completion rate

analysis completion rate

percentage of candidates reaching match calculation

assessment submission rate

score uplift after assessment

employer open-to-invite conversion

time-to-first-shortlist

ratio of interview invites among good_match and strong_match

explanation usefulness rating

mock-vs-live parity incidents

Самопроверка документа.

MUST scope реалистичен за 5 дней: да, потому что стек фиксирован, infra урезана, одна роль и один demo path.

Противоречия: не выявлены.

Неопределенные технологии: нет; стек зафиксирован.

Формулы детерминированы: да.

AI outputs имеют схемы: да.

Endpoints связаны с UI flows: да.

Enterprise-функции в MUST scope: убраны.

Demo mode независим от внешнего API: да.

LLM не принимает hiring decision: да, по конструкции и по контракту.

[1] docker compose up | Docker Docs

https://docs.docker.com/reference/cli/docker/compose/up/?utm_source=chatgpt.com

[2] Next.js Docs: App Router | Next.js

https://nextjs.org/docs/app?utm_source=chatgpt.com

[3] Pydantic V2 Pre Release - Pydantic

https://docs.pydantic.dev/2.3/blog/pydantic-v2-alpha/?utm_source=chatgpt.com

[4] SQLAlchemy ORM — SQLAlchemy 2.0 Documentation

https://docs.sqlalchemy.org/en/20/orm/?utm_source=chatgpt.com

[5] [7] Фоновые задачи - FastAPI

https://fastapi.tiangolo.com/ru/tutorial/background-tasks/?utm_source=chatgpt.com

[6] UploadFile class - FastAPI

https://fastapi.tiangolo.com/reference/uploadfile/?utm_source=chatgpt.com