# BeyondResume

BeyondResume — веб-приложение для evidence-based hiring. Оно помогает кандидату собрать подтверждённый профиль навыков, а работодателю — сопоставить этот профиль с требованиями вакансии. Система объединяет сведения из PDF-резюме и публичных GitHub-репозиториев, а не опирается только на заявленные технологии.

Кандидат подключает несколько репозиториев и загружает резюме. После анализа приложение формирует **Skill Passport**: список навыков с confidence, источниками доказательств и деталями по репозиториям. Работодатель создаёт вакансии и требования, просматривает matches и evidence-backed профиль кандидата.

В проекте есть роли **candidate** и **employer**. Для работодателя доступен AI Hiring Intelligence — read-only анализ для подготовки технического интервью, построенный поверх уже рассчитанного Skill Passport. AI не получает исходный код, README и PDF-файлы кандидата.

## Возможности

- регистрация, вход и JWT-аутентификация;
- отдельные рабочие пространства кандидата и работодателя;
- профиль кандидата;
- загрузка и обработка PDF-резюме (до 8 MiB);
- подключение нескольких публичных GitHub-репозиториев с нормализацией URL;
- запуск и повторный запуск анализа каждого репозитория;
- сохранение GitHub snapshots, evidence и статусов jobs;
- детерминированное извлечение навыков из репозиториев;
- **Skill Passport** с confidence, evidence, источниками и repository breakdown;
- карьерная roadmap кандидата;
- просмотр вакансий и детерминированное сопоставление с ними;
- Employer Workspace: компания, вакансии, требования, matches и Candidate Review;
- AI Hiring Intelligence для выбранных кандидата и вакансии;
- Alembic-миграции и автоматизированные backend/frontend тесты.

## Архитектура

~~~text
Next.js / React frontend
            │
            ▼
       REST API (/api/v1)
            │
            ▼
FastAPI backend ───────► PostgreSQL
    │        │
    │        ├── SQLAlchemy ORM + Alembic migrations
    │        ├── GitHub snapshot / evidence / Skill Passport services
    │        └── resume parsing and background job services
    │
    └── OpenAI provider (только AI Hiring Intelligence)
~~~

| Слой | Ответственность |
| --- | --- |
| frontend/ | Next.js-интерфейс, страницы ролей, React Query-клиент, формы и визуализация evidence. Запросы API проходят через Next.js rewrite /api/v1/*. |
| backend/app/api/ | REST endpoint-ы, аутентификация, проверка роли и владения данными. |
| backend/app/services/ | Сервисы резюме, GitHub scans, evidence, Skill Passport, matching, roadmap и AI Hiring Intelligence. |
| backend/app/integrations/ | Границы внешних интеграций GitHub и OpenAI. |
| backend/app/models/ и schemas/ | SQLAlchemy-модели и Pydantic DTO/response-схемы. |
| backend/alembic/ | Версионированная схема PostgreSQL. |
| PostgreSQL | Пользователи, профили, вакансии, evidence, snapshots, jobs и проекции Skill Passport. |

## Стек технологий

### Frontend

- Next.js 15;
- React 19;
- TypeScript;
- Tailwind CSS, PostCSS и Autoprefixer;
- TanStack React Query;
- Zod;
- Vitest, Testing Library и JSDOM;
- ESLint с eslint-config-next.

### Backend

- Python 3.12+;
- FastAPI и Uvicorn;
- SQLAlchemy 2;
- Pydantic 2 и pydantic-settings;
- Alembic;
- Psycopg 3;
- PyJWT и Argon2;
- pypdf, python-docx и python-multipart;
- официальный Python SDK OpenAI;
- pytest, HTTPX, Ruff, Black и mypy.

### База данных и инфраструктура

- PostgreSQL 16;
- Docker и Docker Compose;
- Docker-образы python:3.12-slim и node:24-alpine.

## Структура проекта

~~~text
backend/
  alembic/                 # миграции базы данных
  app/
    api/                   # REST API v1 и зависимости авторизации
    core/                  # настройки и безопасность
    db/                    # сессии БД и базовые модели
    integrations/          # GitHub и OpenAI provider-ы
    models/                # SQLAlchemy-модели
    prompts/               # prompt-шаблоны AI Hiring Intelligence
    schemas/               # Pydantic DTO и response-схемы
    services/              # доменные сервисы и jobs
    utils/                 # детерминированные extractor-ы и утилиты
  tests/                   # backend тесты

frontend/
  app/                     # Next.js routes и layout
  components/              # общие UI-компоненты
  features/                # candidate, employer, GitHub, resume и passport UI
  lib/                     # API-клиент, типы и hooks
  public/                  # статические ресурсы
  styles/                  # глобальные стили
  tests/                   # Vitest-тесты интерфейса

fixtures/                  # локальные fixtures для тестов
infra/                     # инфраструктурные заготовки
docker-compose.yml         # frontend, backend и PostgreSQL
.env.example               # пример backend/Docker-переменных окружения
frontend/.env.example      # пример переменных Next.js
~~~

## Пользовательские сценарии

Ниже описаны реальные сценарии текущего интерфейса. Формулировки кнопок в интерфейсе могут быть на английском; названия приведены в скобках, чтобы их было проще найти.

### Общий вход в систему

1. Откройте главную страницу приложения.
2. Если аккаунта ещё нет, перейдите на страницу регистрации (`/register`).
3. Выберите тип аккаунта: кандидат (**candidate**) или работодатель (**employer**).
4. Укажите email, пароль, подтверждение пароля и подтвердите обязательные условия формы.
5. После регистрации войдите через страницу `/login`.
6. После успешной аутентификации приложение открывает рабочее пространство, соответствующее роли. Роль определяет доступные данные и действия: кандидат управляет только собственным профилем и evidence, работодатель — только своей компанией, вакансиями и доступными match-результатами.

### Сценарий кандидата: от профиля до Skill Passport

#### 1. Заполнить профиль кандидата

1. В Candidate Workspace откройте страницу профиля (`/profile`) или перейдите к разделу **Candidate Profile** на рабочей странице.
2. Заполните доступные поля профиля и сохраните изменения.
3. Это необходимо до подключения GitHub и добавления резюме: evidence привязывается к профилю кандидата, а не только к учётной записи.

#### 2. Подключить и проанализировать GitHub-репозиторий

1. На главной странице Candidate Workspace перейдите к секции **GitHub**.
2. Введите URL публичного репозитория GitHub в поле **Repository URL**.
3. Нажмите **Connect repository**.
4. Подключение нормализует GitHub URL; один и тот же репозиторий нельзя подключить дважды к одному профилю, включая варианты с `.git`, завершающим `/` или SSH-формой URL.
5. В карточке подключённого репозитория запустите **Analyze**. Для каждого репозитория создаётся отдельная job, поэтому анализ нескольких репозиториев выполняется и отображается раздельно.
6. Дождитесь статуса `Completed`. В деталях репозитория будут доступны snapshot, найденные навыки и evidence.
7. Чтобы обновить данные только одного репозитория, используйте **Re-run analysis** в его карточке. Evidence остальных подключений сохраняется.
8. При необходимости удалите конкретное подключение кнопкой **Delete**. Удаляются только evidence и snapshots этого репозитория; данные остальных репозиториев остаются в профиле.
9. Чтобы усилить профиль, повторите шаги 2–8 для дополнительных публичных репозиториев.

#### 3. Добавить резюме как дополнительный источник evidence

1. На главной странице Candidate Workspace найдите секцию **Resume**.
2. Выберите PDF-файл в поле **Resume file**. Приложение принимает только PDF размером до 8 MiB.
3. Нажмите **Add resume evidence**.
4. Пока задача обработки выполняется, в секции отображается её статус. После успешного завершения резюме становится дополнительным источником evidence.
5. При повторной загрузке нажмите **Replace resume**. Новое актуальное резюме заменяет предыдущее; GitHub-подключения и их evidence не удаляются.
6. Если обработка завершилась ошибкой, используйте доступную кнопку **Retry processing** после устранения причины ошибки.

#### 4. Просмотреть Skill Passport и evidence

1. Откройте страницу `/skill-passport` или используйте ссылку **View full passport** из обзора.
2. В Skill Passport просмотрите подтверждённые навыки, их общий confidence и источники доказательств.
3. Используйте существующий поиск и фильтры, если нужно сузить список по названию, категории или источнику.
4. Нажмите **Open evidence** у навыка, чтобы открыть технические детали: evidence units, источники и GitHub repository breakdown.
5. Общий confidence навыка агрегируется по всем доступным источникам. Repository confidence относится только к evidence конкретного репозитория и не является долей общего процента.
6. Если подключены несколько репозиториев, одинаковый навык может быть подтверждён несколькими из них; это отображается в details навыка.

#### 5. Использовать roadmap и вакансии

1. В Candidate Workspace откройте секцию **Roadmap**. Она показывает существующие детерминированные рекомендации на основе текущего Skill Passport.
2. Для просмотра доступных вакансий перейдите на `/vacancies`.
3. В карточке вакансии отображается текущий **Vacancy match**, обязательные навыки и известные gaps.
4. Нажмите **View details**, чтобы увидеть требования вакансии, matched/missing skills и связанную Vacancy Roadmap.
5. Vacancy match — это показатель соответствия вакансии; он не заменяет confidence отдельного навыка из Skill Passport.

### Сценарий работодателя: от компании до Candidate Review

#### 1. Создать компанию и вакансию

1. Войдите под учётной записью employer. Главная страница открывает Employer Workspace.
2. В блоке компании заполните доступную форму и сохраните данные компании, если она ещё не создана.
3. В Employer Dashboard воспользуйтесь существующим действием создания вакансии (**Create vacancy**).
4. Укажите доступные поля вакансии, включая название и описание, затем сохраните её.
5. В списке вакансий выберите нужную карточку и нажмите **Manage vacancy**. Карточки остаются компактными, а выбранная вакансия открывается в отдельном **Selected vacancy workspace** ниже списка.

#### 2. Настроить требования вакансии

1. В рабочем пространстве выбранной вакансии откройте блок **Requirements**.
2. Выберите навык из существующего каталога ontology.
3. Укажите тип требования: **Required** для обязательного навыка или **Preferred** для желательного.
4. Нажмите **Add requirement**.
5. Добавленные требования отображаются раздельно в группах Required skills и Preferred skills.
6. Для удаления требования используйте действие **Remove** рядом с ним.
7. Если требований нет, интерфейс явно показывает, что meaningful candidate matching ещё не настроен. Добавьте требования перед оценкой match-результатов.

#### 3. Просмотреть candidates, сопоставленные с вакансией

1. В том же рабочем пространстве откройте блок **Candidate matches**.
2. Список содержит только результаты для выбранной вакансии и сохраняет порядок, полученный из существующего Matching Engine.
3. В каждой карточке видны Vacancy match, количество matched/missing required skills и matched/missing preferred skills.
4. Нажмите **Review candidate**, чтобы открыть read-only Candidate Review. Ссылка сохраняет контекст выбранной вакансии через параметр `vacancy_id`.
5. Если candidates для вакансии нет, интерфейс показывает фактическое состояние **No candidate matches yet**; он не создаёт фиктивных кандидатов или процентов.

#### 4. Провести Candidate Review

1. На странице `/employer/matches/{candidate_id}?vacancy_id={vacancy_id}` проверьте имя кандидата и контекст вакансии.
2. Сначала интерпретируйте **Vacancy match** — это детерминированное соответствие кандидата требованиям именно выбранной вакансии.
3. Откройте **Skill Passport** кандидата. Для каждого employer-visible навыка отображаются existing evidence confidence, прогресс, число evidence items и source badges.
4. Сверяйте relevance-названия: **Required · Matched**, **Preferred · Matched** или **Additional skill**. Отсутствующие требования показаны отдельно и не получают фиктивный `0%` skill confidence.
5. Используйте **Skill comparison** для просмотра matched, partially matched и missing требований.
6. Выберите навык в таблице или Skill Passport, чтобы отфильтровать существующий блок **Evidence behind the match**. Работодатель получает только разрешённые evidence details и не может редактировать профиль кандидата.
7. Просмотрите существующую roadmap в боковой колонке, если она есть для этого match-контекста.

#### 5. Открыть AI Hiring Intelligence

1. На Candidate Review перейдите на вкладку **AI Hiring**. Она сохраняет те же `candidate_id` и `vacancy_id`.
2. Откроется адрес `/employer/matches/{candidate_id}/ai-hiring?vacancy_id={vacancy_id}`.
3. Страница запрашивает AI Hiring Intelligence только для выбранных кандидата и вакансии, которыми владеет текущий employer.
4. При успешном ответе просмотрите **Technical Interview Recommendation**, confidence, summary, strengths, concerns и interview questions.
5. AI-рекомендация является вспомогательной информацией для технического интервью. Она не равна Vacancy match, не является окончательным решением о найме и не должна быть единственным основанием решения.
6. Если AI provider недоступен, интерфейс показывает безопасное сообщение о временной недоступности и не заменяет результат выдуманной рекомендацией.
7. Вернитесь на вкладку **Candidate Review**, чтобы продолжить работу с детерминированными match и evidence данными без потери vacancy context.

### Краткая карта действий

| Роль | Начальное действие | Следующий результат |
| --- | --- | --- |
| Candidate | Заполнить профиль | можно подключить GitHub и добавить resume evidence |
| Candidate | Подключить и завершить GitHub analysis | Skill Passport получает GitHub evidence |
| Candidate | Добавить PDF-резюме | Skill Passport получает дополнительный источник evidence |
| Candidate | Открыть vacancies | видны existing Vacancy match и gaps |
| Employer | Создать компанию и вакансию | доступно управление вакансией |
| Employer | Добавить Required/Preferred requirements | появляются scoped candidate matches |
| Employer | Открыть Candidate Review | доступны Skill Passport, evidence и roadmap кандидата |
| Employer | Открыть AI Hiring | доступна рекомендация для технического интервью в контексте вакансии |

## Локальный запуск

### Предварительные требования

- Git;
- Docker Desktop с Docker Compose **или** PostgreSQL 16, Python 3.12+ и Node.js 24+;
- npm для frontend;
- ключ OpenAI нужен только для реального AI Hiring Intelligence.

### 1. Клонирование

~~~bash
git clone <URL_вашего_репозитория>
cd BeyondResume
~~~

### 2. Быстрый запуск через Docker Compose

Создайте файл конфигурации из примера и замените JWT_SECRET на длинную случайную строку:

~~~bash
cp .env.example .env
docker compose up --build
~~~

В Windows PowerShell:

~~~powershell
Copy-Item .env.example .env
docker compose up --build
~~~

Compose запускает frontend на http://localhost:3000, backend на http://localhost:8000 и PostgreSQL на localhost:5432.

После первого старта примените миграции и заполните базовую ontology навыков:

~~~bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_skill_ontology
~~~

### 3. Ручной запуск backend

~~~bash
cd backend
python -m venv .venv
~~~

macOS/Linux:

~~~bash
source .venv/bin/activate
~~~

Windows PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
~~~

Установите приложение и инструменты разработки:

~~~bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
~~~

Скопируйте корневой .env.example в .env. Для PostgreSQL, запущенного на хосте, укажите 127.0.0.1 вместо Docker hostname postgres:

~~~dotenv
DATABASE_URL=postgresql+psycopg://ebh:ebh@127.0.0.1:5432/ebh
~~~

Примените миграции, создайте ontology и запустите API:

~~~bash
alembic upgrade head
python -m app.scripts.seed_skill_ontology
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

### 4. Ручной запуск frontend

В отдельном терминале:

~~~bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
~~~

В Windows PowerShell:

~~~powershell
Copy-Item .env.example .env.local
npm install
npm run dev
~~~

API_UPSTREAM в frontend/.env.local должен указывать на backend:

~~~dotenv
API_UPSTREAM=http://localhost:8000
~~~

### 5. Проверка

| Адрес | Назначение |
| --- | --- |
| http://localhost:3000 | интерфейс BeyondResume |
| http://localhost:8000/docs | Swagger UI FastAPI |
| http://localhost:8000/openapi.json | OpenAPI-спецификация |

## Переменные окружения

Backend читает корневой .env, а также поддерживает backend/.env. Шаблон находится в .env.example. Не добавляйте .env в Git и не публикуйте секреты.

| Переменная | Назначение | Локальное значение / примечание |
| --- | --- | --- |
| DATABASE_URL | строка подключения SQLAlchemy/Psycopg к PostgreSQL | postgresql+psycopg://ebh:ebh@127.0.0.1:5432/ebh |
| JWT_SECRET | обязательный секрет подписи access token | длинная случайная строка |
| JWT_ACCESS_TTL_MINUTES | срок действия access token в минутах | 15 |
| UPLOAD_DIR | каталог загруженных резюме | доступный каталог; в Docker — /app/data/uploads |
| RESUME_PARSE_TIMEOUT_SECONDS | тайм-аут обработки резюме в секундах | 20 |
| GITHUB_PROVIDER | источник GitHub-данных: live или demo | live |
| GITHUB_TOKEN | необязательный Bearer token для публичного GitHub API | пустая строка или токен |
| GITHUB_API_TIMEOUT_SECONDS | тайм-аут GitHub API в секундах | 20 |
| OPENAI_API_KEY | ключ OpenAI для AI Hiring Intelligence | обязателен для реального AI-анализa |
| OPENAI_MODEL | модель OpenAI для AI Hiring Intelligence | gpt-5-mini |
| LLM_PROVIDER | provider AI match explanation: mock или openai | mock для локальной разработки |
| LLM_API_KEY | ключ provider-а при LLM_PROVIDER=openai | пустая строка или ключ |
| LLM_MODEL | модель AI match explanation | gpt-5-mini |
| LLM_TIMEOUT_SECONDS | тайм-аут LLM-запросов в секундах | 20 |
| DEMO_MODE | настройка demo-режима backend | true |

Frontend использует серверную переменную Next.js:

| Переменная | Назначение |
| --- | --- |
| API_UPSTREAM | адрес FastAPI для rewrite запросов /api/v1/*; по умолчанию http://localhost:8000 |

Лимит загрузки PDF в приложении составляет 8 MiB. Поддерживается только PDF.

## Тестирование и проверки

### Backend

Выполняйте из backend/ после активации виртуального окружения:

~~~bash
pytest
ruff check app tests
alembic heads
~~~

### Frontend

Выполняйте из frontend/ после npm install:

~~~bash
npm run test
npm run typecheck
npm run lint
npm run build
~~~

npm run build собирает production-версию Next.js, а npm run start запускает уже собранное приложение.

## Используемые AI-сервисы

OpenAI используется только в employer-функции **AI Hiring Intelligence**. Backend передаёт provider-у компактный CandidateHiringContext, построенный из уже рассчитанного Skill Passport: навыков, confidence и краткой сводки evidence.

AI-сервис формирует структурированный ответ с рекомендацией о техническом интервью и списком вопросов. Он не получает исходный код GitHub-репозиториев, README, PDF-резюме, ORM-модели или секреты. Ответ проходит Pydantic- и семантическую валидацию; при недоступности provider-а интерфейс получает контролируемый статус unavailable, а не фиктивный результат.

## Лицензия

В репозитории нет файла лицензии. Условия использования и распространения следует согласовать с владельцем проекта до публикации или повторного использования кода.
