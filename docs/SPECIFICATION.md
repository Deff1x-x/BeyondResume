# BeyondResume — Unified Product, Business and Technical Specification

**Версия:** 4.0  
**Статус:** Execution-ready specification for 5-day Hackathon MVP  
**Дата:** 17 июля 2026  
**Язык реализации MVP:** русский интерфейс с готовностью к i18n  
**Назначение:** единый источник требований для продукта, дизайна, frontend, backend, AI, аналитики, монетизации и дальнейших этапов разработки.

---

## 0. Правила использования документа

Этот документ заменяет разрозненные продуктовые решения и становится основным источником истины для BeyondResume.

Документ определяет:

- какую проблему решает продукт;
- кто является пользователем, покупателем и плательщиком;
- как устроен полный жизненный цикл кандидата и работодателя;
- какие данные являются доказательствами навыков;
- как формируются Skill Passport, Match Score и Confidence Score;
- какие решения разрешено принимать AI;
- какие функции входят в Hackathon MVP, Commercial MVP и последующие версии;
- как продукт монетизируется;
- какие ограничения, тарифы и usage-события должны поддерживаться сайтом;
- какие API, таблицы, страницы и статусы должны существовать;
- какие метрики определяют успех продукта.

### 0.1 Нормативные термины

- **MUST** — обязательное требование.
- **MUST NOT** — запрещённое поведение.
- **SHOULD** — рекомендуемое требование, которое допускается отложить только с явным решением.
- **MAY** — опциональная функция.
- **Hackathon MVP** — демонстрационная end-to-end версия.
- **Commercial MVP** — первая версия, которую можно продавать реальным компаниям.
- **Post-MVP** — функции, которые не должны блокировать запуск.

### 0.2 Приоритет требований

При конфликте требований применяется следующий порядок:

1. безопасность, законность и права кандидата;
2. детерминированность и объяснимость scoring;
3. целостность данных;
4. продуктовая бизнес-логика;
5. коммерческая логика и ограничения тарифов;
6. UX;
7. техническая оптимизация.

### 0.3 Запрет на самостоятельное расширение бизнес-логики

Разработчик или AI-ассистент MUST NOT:

- придумывать новые формулы scoring;
- добавлять скрытые штрафы;
- использовать защищённые характеристики;
- автоматически отклонять кандидатов;
- менять тарифные ограничения;
- вводить новые роли;
- добавлять платные ограничения кандидату;
- менять жизненные циклы сущностей;
- перестраивать архитектуру без изменения этого документа.

Недоопределённое поведение должно быть вынесено на уточнение, а не реализовано по предположению.

---

# Часть I. Продукт и рынок

## 1. Название и категория продукта

**Название:** BeyondResume  
**Категория:** Evidence-Based Talent Intelligence для найма junior IT-специалистов.

BeyondResume не является:

- конструктором резюме;
- обычным job board;
- полноценной ATS в первой версии;
- автоматическим судьёй кандидатов;
- платформой, где LLM самостоятельно принимает решение о найме.

BeyondResume является слоем оценки качества сигнала между входящим потоком кандидатов и решением рекрутера.

## 2. Проблема

### 2.1 Проблема кандидата

У junior-кандидата недостаточно формального опыта, поэтому обычное резюме слабо отражает его реальную готовность к работе.

Полезные доказательства часто разбросаны по разным источникам:

- резюме;
- GitHub;
- pet-проекты;
- учебные проекты;
- стажировки;
- сертификаты;
- хакатоны;
- open-source contributions;
- технические задания;
- рекомендации.

Кандидат не понимает:

- какие навыки действительно подтверждены;
- какие навыки только заявлены;
- на какие вакансии он подходит сейчас;
- почему он не проходит первичный отбор;
- какие действия сильнее всего повысят его готовность.

### 2.2 Проблема работодателя

Работодатель получает большое количество junior-резюме с похожими формулировками и не может быстро определить реальный уровень кандидатов.

Ручная проверка требует:

- открыть резюме;
- проверить ссылки;
- просмотреть GitHub;
- оценить проекты;
- проверить соответствие вакансии;
- сформировать вопросы для интервью.

В результате:

- screening занимает много времени;
- хорошие кандидаты теряются из-за слабого оформления;
- красивые self-claims получают слишком высокий вес;
- hiring managers повторяют одну и ту же проверку;
- решение сложно объяснить и защитить.

### 2.3 Экономическая проблема

Экономический ущерб создаётся не только неправильным наймом, но и стоимостью первичной обработки потока:

- часы рекрутера и hiring manager;
- задержка закрытия вакансии;
- стоимость внешних assessment-инструментов;
- повторная работа при слабом shortlist;
- потеря подходящих кандидатов;
- плохой candidate experience.

BeyondResume должен продавать не «AI-анализ резюме», а сокращение стоимости и времени первичного отбора при сохранении человеческого контроля.

## 3. Миссия

> BeyondResume помогает компаниям оценивать начинающих IT-специалистов по проверяемым доказательствам навыков, а кандидатам — понимать и закрывать конкретные пробелы до желаемой роли.

## 4. Ценностное предложение

### 4.1 Для кандидата

BeyondResume превращает разрозненные достижения в единый Skill Passport и показывает:

- подтверждённые навыки;
- силу доказательств;
- соответствие конкретным вакансиям;
- критические пробелы;
- следующий наиболее полезный шаг;
- изменение результата после нового evidence или assessment.

### 4.2 Для работодателя

BeyondResume превращает поток резюме в объяснимый shortlist:

- ранжирование по требованиям вакансии;
- отдельный Match Score и Confidence Score;
- подтверждения по каждому навыку;
- критические gaps;
- причины высокого или низкого результата;
- возможность запросить дополнительное доказательство;
- история действий и human decision.

### 4.3 Одно предложение для продаж

> BeyondResume сокращает время первичного отбора junior IT-кандидатов, превращая резюме, GitHub и проекты в объяснимый профиль навыков и сопоставляя его с требованиями вакансии.

## 5. Продуктовые принципы

1. **Evidence over assertion.** Подтверждение сильнее self-claim.
2. **Human-in-the-loop.** Система помогает принимать решение, но не нанимает и не отклоняет автоматически.
3. **Explainability by default.** Каждое число должно раскрываться до факторов и evidence.
4. **Missing data is uncertainty, not incompetence.** Отсутствие данных снижает confidence, но не является доказательством слабого уровня.
5. **Deterministic final scoring.** Финальные числа вычисляет backend по версионированным формулам.
6. **AI as extraction layer.** AI извлекает, классифицирует и объясняет, но не устанавливает бизнес-правила.
7. **Candidate transparency.** Кандидат видит, какие данные используются и может исправить ошибку.
8. **Minimal sensitive data.** Защищённые характеристики не используются в scoring.
9. **Commercial discipline.** Платформа должна измерять usage, стоимость обработки и полученную клиентом ценность.
10. **Integration, not replacement.** Коммерческая версия сначала дополняет ATS, а не пытается заменить её.

---

# Часть II. Пользователи, роли и доступ

## 6. Роли

### 6.1 Candidate

Candidate может:

- зарегистрироваться;
- редактировать профиль;
- загружать резюме;
- подключать evidence sources;
- запускать анализ;
- видеть Skill Passport;
- видеть match по доступным вакансиям;
- проходить assessments;
- получать roadmap;
- управлять видимостью профиля;
- отзывать согласие и удалять данные;
- оспаривать неверно извлечённое evidence.

Candidate MUST NOT видеть:

- закрытые заметки рекрутера;
- других кандидатов;
- внутренний ranking работодателя;
- конфиденциальные настройки вакансии.

### 6.2 Employer Member / Recruiter

Recruiter может:

- работать внутри одной или нескольких организаций, к которым приглашён;
- создавать и редактировать вакансии в рамках прав;
- просматривать кандидатов только в контексте вакансий организации;
- видеть Match, Confidence и evidence explanations;
- добавлять кандидата в shortlist;
- запрашивать дополнительное evidence;
- отправлять приглашение;
- фиксировать этапы hiring pipeline;
- оставлять внутренние заметки.

Recruiter MUST NOT:

- просматривать весь глобальный каталог кандидатов без разрешения кандидатов и соответствующего тарифа;
- видеть защищённые характеристики;
- экспортировать больше данных, чем разрешает тариф и политика;
- автоматически отклонять кандидата только по score.

### 6.3 Company Admin

Company Admin имеет права Recruiter и дополнительно может:

- управлять организацией;
- приглашать и удалять участников;
- назначать роли;
- управлять подпиской;
- видеть usage и billing;
- управлять API keys и интеграциями;
- управлять retention policy в разрешённых пределах;
- экспортировать audit data.

### 6.4 Platform Admin

Platform Admin существует только для эксплуатации сервиса.

Он может:

- просматривать технические статусы;
- управлять тарифами через административную конфигурацию;
- просматривать агрегированную аналитику;
- обрабатывать запросы поддержки;
- блокировать злоупотребления;
- запускать повторную обработку jobs.

Platform Admin MUST NOT изменять Match Score вручную без audit event и явной причины.

### 6.5 Будущие роли

Следующие роли не входят в Hackathon MVP:

- Agency Admin;
- University Admin;
- Mentor;
- Auditor;
- Integration Service Account.

Они могут быть добавлены только после расширения этой спецификации.

## 7. Организации и tenancy

Commercial MVP MUST поддерживать multi-tenant модель.

Основные правила:

- каждый работодатель действует внутри `organization`;
- пользователь может состоять в нескольких организациях;
- вакансия принадлежит ровно одной организации;
- billing account принадлежит организации;
- usage считается на уровне организации;
- кандидаты не принадлежат работодателю;
- application связывает кандидата и вакансию;
- данные одной организации не должны быть доступны другой;
- все employer API обязаны проверять membership и permission.

Hackathon MVP MAY использовать упрощённую модель, где employer profile фактически соответствует одной организации, но новая схема не должна блокировать переход к multi-tenant.

---

# Часть III. Основная бизнес-логика

## 8. Главный продуктовый цикл

```mermaid
flowchart LR
    A[Candidate Profile] --> B[Evidence Collection]
    B --> C[Evidence Graph]
    C --> D[Skill Passport]
    D --> E[Vacancy Matching]
    E --> F[Match + Confidence + Gaps]
    F --> G[Assessment or New Evidence]
    G --> C

    H[Employer Vacancy] --> I[Structured Requirements]
    I --> E
    F --> J[Recruiter Review]
    J --> K[Shortlist / Request Evidence / Invite / Reject]
    K --> L[Outcome Feedback]
```

## 9. Жизненный цикл кандидата

### 9.1 Регистрация

Candidate регистрируется по email и паролю.

После регистрации:

- создаётся user;
- создаётся candidate profile;
- onboarding status = `profile_required`;
- профиль не публикуется автоматически;
- marketing consent не включается по умолчанию.

### 9.2 Onboarding

Минимальные поля:

- display name;
- target role;
- location или remote preference;
- English level;
- availability;
- короткий summary;
- consent на обработку данных.

Необязательные поля:

- salary expectation;
- preferred employment type;
- relocation readiness;
- portfolio URL;
- LinkedIn URL.

### 9.3 Загрузка резюме

Кандидат загружает PDF или DOCX.

После успешной загрузки:

1. создаётся Resume;
2. создаётся Job типа `resume_parse`;
3. статус Resume = `uploaded`;
4. файл сохраняется неизменённым;
5. parsing выполняется асинхронно;
6. при успехе Resume = `parsed`;
7. при неуспехе Resume = `failed`;
8. ошибка должна быть понятна пользователю и пригодна для повторной попытки.

#### Plain-text parsing: граница текущего MVP

Текущий MVP реализует только безопасное асинхронное извлечение plain text из загруженного Resume.

`POST /candidate/resumes/{resume_id}/parse` запускает обработку Resume только через Job типа
`resume_parse`: endpoint создаёт pending Job либо возвращает существующий активный Job в
соответствии с idempotency-логикой. Endpoint не выполняет parsing синхронно и не возвращает
извлечённый текст.

Worker берёт pending Job, переводит его в `running`, извлекает plain text существующим parser
service и сохраняет текст только во внутреннем поле `Resume.extracted_text`. При успехе одной
транзакцией выполняются `Job: running → completed` и `Resume: uploaded → parsed`; при ошибке —
`Job: running → failed` и `Resume: uploaded → failed`.

Для этого MVP Resume имеет только переходы `uploaded → parsed` и `uploaded → failed`. Статус
`parsing` не используется. `GET /jobs/{job_id}` — единственный публичный способ polling
состояния обработки; отдельный endpoint результата parsing не нужен. Полный
`Resume.extracted_text` не публикуется через публичный API и предназначен для будущих внутренних
этапов обработки.

### 9.4 Evidence collection

Structured extraction и Evidence collection не входят в текущий plain-text parsing worker и
реализуются отдельными последующими модулями. После их реализации система сможет извлекать
потенциальные claims:

- skills;
- projects;
- experience;
- education;
- certificates;
- achievements;
- links.

Каждый claim из резюме первоначально является `self_claimed`, пока не связан с более сильным evidence.

Кандидат может добавить:

- публичный GitHub repository;
- GitHub profile;
- project URL;
- certificate URL или файл;
- hackathon participation;
- assessment submission;
- work sample;
- reference.

### 9.5 Анализ профиля

Кнопка **Analyze profile** доступна, когда:

- есть успешно распарсенное резюме;
- пользователь принял обязательные согласия;
- нет активного анализа того же snapshot;
- не превышены ограничения защиты от злоупотреблений.

После запуска:

1. создаётся immutable profile snapshot;
2. создаётся analysis job;
3. собираются источники evidence;
4. AI извлекает и нормализует сущности;
5. deterministic validators проверяют структуру;
6. строится Evidence Graph;
7. backend рассчитывает skill scores и confidence;
8. создаётся версия Skill Passport;
9. активные match results пересчитываются;
10. usage event фиксируется.

### 9.6 Skill Passport

Кандидат получает:

- target role;
- список skills;
- уровень каждого skill;
- confidence;
- evidence strength;
- источники;
- дату последнего подтверждения;
- статус `claimed`, `supported`, `verified` или `assessed`;
- профильные strengths;
- области неопределённости;
- completeness score.

### 9.7 Поиск и match вакансий

Кандидат может:

- открыть опубликованную вакансию;
- увидеть eligibility;
- запустить match, если он ещё не рассчитан;
- увидеть Match Score;
- увидеть Confidence Score;
- увидеть critical gaps;
- увидеть рекомендованные действия.

Кандидат не должен видеть внутренние веса, которые работодатель пометил confidential, но должен видеть понятное объяснение причины результата.

### 9.8 Assessment

Assessment может быть:

- системным шаблоном;
- заданием работодателя;
- рекомендованным заданием для закрытия gap.

В Hackathon MVP поддерживается одно текстовое задание с отправкой GitHub URL и explanation.

После submission:

1. выполняются deterministic checks;
2. AI выполняет rubric review в пределах рубрики;
3. backend рассчитывает assessment result;
4. assessment evidence добавляется в Evidence Graph;
5. Skill Passport и Match пересчитываются;
6. кандидат видит `before` и `after`.

Пользовательский код в MVP MUST NOT исполняться.

### 9.9 Roadmap

Roadmap строится из 3–5 действий.

Каждое действие содержит:

- gap;
- причину важности;
- конкретный deliverable;
- ориентировочную сложность;
- ожидаемый эффект на readiness;
- способ доказать выполнение.

Roadmap не должен обещать гарантированный рост score, если результат зависит от качества будущего evidence.

### 9.10 Видимость профиля

Возможные статусы:

- `private` — доступен только кандидату;
- `applications_only` — виден работодателям, куда кандидат откликнулся;
- `discoverable` — может быть найден работодателями в разрешённых сценариях;
- `paused` — скрыт из discovery, существующие applications сохраняются.

По умолчанию: `applications_only`.

## 10. Жизненный цикл работодателя

### 10.1 Регистрация и организация

Employer регистрируется и:

- создаёт organization или принимает приглашение;
- подтверждает email;
- указывает company name, website, size и country;
- назначается Company Admin при создании организации;
- получает trial или free sandbox, если он предусмотрен pricing policy.

### 10.2 Trial

Рекомендуемая коммерческая политика:

- 14 дней;
- одна опубликованная вакансия;
- до 50 анализов кандидатов;
- до 2 seats;
- без API;
- без bulk export;
- карта не обязательна для design partners и pilot;
- карта может быть обязательной для публичного self-serve trial после доказанного PMF.

Trial превращается в paid только по явному согласию.

### 10.3 Создание вакансии

Вакансия создаётся в статусе `draft`.

Обязательные поля:

- title;
- role family;
- seniority;
- description;
- employment type;
- location/remote policy;
- language requirements;
- at least one must-have requirement;
- application visibility;
- status.

Каждое требование содержит:

- normalized skill или constraint;
- category;
- requirement type: `must_have`, `nice_to_have`, `constraint`;
- target level;
- weight;
- hard filter flag;
- evidence expectation;
- recruiter explanation.

### 10.4 Нормализация вакансии

Работодатель может вставить текст вакансии.

AI может предложить:

- skills;
- уровни;
- must-have/nice-to-have;
- constraints;
- дубли;
- слишком общие требования.

Но работодатель обязан подтвердить структуру перед публикацией.

### 10.5 Публикация вакансии

Публикация разрешена, если:

- organization active;
- subscription допускает новую active vacancy;
- обязательные поля заполнены;
- есть must-have;
- веса валидны;
- запрещённые критерии отсутствуют;
- recruiter подтвердил требования.

После публикации:

- vacancy status = `published`;
- открывается приём applications;
- существующие подходящие кандидаты MAY быть рассчитаны в background;
- usage учитывается только при фактическом анализе кандидата, а не при создании пустой вакансии.

### 10.6 Работа с кандидатами

Recruiter видит таблицу:

- candidate;
- Match Score;
- Confidence Score;
- critical gaps;
- top evidence;
- application stage;
- last updated;
- flags requiring human review.

Сортировка по умолчанию:

1. eligibility;
2. Match Score descending;
3. Confidence Score descending;
4. updated_at descending.

Система MUST NOT скрывать кандидата автоматически из-за низкого score. Допускается фильтр, который recruiter включает вручную.

### 10.7 Действия рекрутера

Поддерживаемые действия:

- open profile;
- shortlist;
- request evidence;
- invite;
- move stage;
- reject with reason;
- restore;
- add note.

Для adverse action система должна сохранить:

- кто принял решение;
- когда;
- reason category;
- optional comment;
- model/scoring version;
- score snapshot;
- confirmation, что решение принято человеком.

### 10.8 Закрытие вакансии

Возможные причины:

- hired;
- cancelled;
- paused;
- duplicate;
- budget closed.

После закрытия:

- новые applications запрещены;
- billing не должен считать вакансию active;
- история и audit сохраняются;
- retention policy применяется по договору и законодательству.

## 11. Application lifecycle

Статусы application:

- `submitted`;
- `screening`;
- `evidence_requested`;
- `shortlisted`;
- `assessment`;
- `interview`;
- `offer`;
- `hired`;
- `rejected`;
- `withdrawn`;
- `archived`.

Правила:

- переходы фиксируются в application events;
- кандидат может withdraw;
- employer не может вернуть withdrawn application без согласия кандидата;
- rejected можно restore только с audit event;
- hired завершает активный pipeline;
- изменение score не должно автоматически менять stage.

---

# Часть IV. Evidence Graph и Skill Passport

## 12. Evidence как основная единица продукта

### 12.1 Evidence Unit

Каждый evidence unit содержит:

- `id`;
- `candidate_id`;
- `source_type`;
- `source_reference`;
- `title`;
- `description`;
- `observed_at`;
- `issued_at`;
- `freshness_at`;
- `verification_status`;
- `ownership_status`;
- `strength_score`;
- `quality_flags`;
- `raw_payload_reference`;
- `created_at`;
- `updated_at`.

`ownership_status` принимает только следующие нормативные значения:

- `unverified` — источник связан с профилем кандидата, но система не получила независимого
  подтверждения владения;
- `verified` — владение источником подтверждено отдельным механизмом, явно определённым в SPEC.

### 12.2 Источники evidence

| Source | Базовая сила | Комментарий |
|---|---:|---|
| Technical assessment | 1.00 | Сильное evidence при валидной рубрике |
| Relevant public code repository | 1.00 | Требуется ownership и содержательный код |
| Verified work sample | 0.95 | Проверяемый артефакт реальной работы |
| Work experience with explicit stack | 0.90 | Сильнее при внешнем подтверждении |
| Detailed project with repository/demo | 0.80 | Зависит от сложности и ownership |
| Hackathon result | 0.70 | Сильнее при публичной проверке |
| Certificate from recognized issuer | 0.50 | Подтверждает обучение, не обязательно практику |
| Course completion | 0.40 | Слабый сигнал без практического артефакта |
| Resume claim only | 0.30 | Self-claim без внешнего подтверждения |

Эти значения являются default configuration v1, а не вечными константами. Изменение требует новой scoring version.

### 12.3 Verification status

- `unverified`;
- `source_reachable`;
- `ownership_confirmed`;
- `issuer_verified`;
- `platform_assessed`;
- `disputed`;
- `invalidated`.

### 12.4 Skill claim

Skill claim связывает:

- candidate;
- normalized skill;
- source evidence;
- extracted context;
- claimed level;
- detected level;
- confidence;
- extraction version.

Один evidence unit может подтверждать несколько skills.

Один skill может подтверждаться несколькими independent evidence units.

## 13. Skill ontology

Система должна нормализовать варианты:

- `Postgres`, `PostgreSQL`, `postgresql` → `PostgreSQL`;
- `JS`, `JavaScript` → `JavaScript`;
- `REST`, `REST API`, `RESTful API` → skill family с контекстом.

Skill содержит:

- canonical name;
- aliases;
- category;
- parent skill;
- related skills;
- deprecated flag;
- version.

Категории MVP:

- programming_language;
- framework;
- database;
- tooling;
- testing;
- architecture;
- cloud_devops;
- computer_science;
- communication;
- language;
- domain.

## 14. Skill level

Уровень хранится в диапазоне 0–4:

- 0 — нет evidence;
- 1 — знакомство / guided use;
- 2 — самостоятельное применение в небольшом проекте;
- 3 — уверенное применение в комплексной задаче;
- 4 — продвинутое применение, системное понимание или leadership.

Для junior product большинство релевантных результатов ожидаются в диапазоне 1–3.

AI может предложить level estimate, но backend применяет правила ограничения по типу evidence.

Пример:

- resume self-claim не может самостоятельно дать итоговый level выше 1;
- один учебный проект не может самостоятельно дать level выше 2;
- verified assessment может подтвердить level до границы рубрики;
- несколько независимых сильных sources могут повысить level.

## 15. Candidate Skill Score

Для skill `s` рассчитываются:

- `level_score` 0–100;
- `evidence_strength` 0–100;
- `confidence` 0–100;
- `freshness` 0–100;
- `consistency` 0–100.

Базовая версия формулы:

```text
candidate_skill_score =
    0.45 * level_score
  + 0.25 * evidence_strength
  + 0.15 * freshness
  + 0.15 * consistency
```

Confidence рассчитывается отдельно и не умножается скрыто на skill score.

### 15.1 Aggregation evidence strength

Для предотвращения простого суммирования слабых источников применяется diminishing returns.

```text
combined_strength = 100 * (1 - Π(1 - adjusted_source_strength_i))
```

Где source strength приведён к диапазону 0–1 и скорректирован на:

- verification;
- ownership;
- relevance;
- freshness;
- duplication.

Дублированные или зависимые источники не считаются полностью независимыми.

## 16. Confidence Score навыка

```text
skill_confidence =
    0.30 * source_diversity
  + 0.25 * evidence_quality
  + 0.15 * extraction_certainty
  + 0.15 * freshness
  + 0.15 * cross_source_consistency
```

Интерпретация:

- 0–39 — low confidence;
- 40–69 — medium confidence;
- 70–84 — high confidence;
- 85–100 — very high confidence.

## 17. Skill Passport

### 17.1 Версионирование

Skill Passport является immutable snapshot.

Каждая версия содержит:

- profile snapshot id;
- evidence snapshot id;
- skill ontology version;
- scoring version;
- AI extraction version;
- generated_at;
- status;
- summary;
- completeness;
- skills.

Новый evidence создаёт новую версию, а не меняет старую историю.

### 17.2 Completeness Score

Completeness не является оценкой способностей.

Он показывает полноту информации:

- profile fields;
- resume;
- at least one project;
- at least one code source;
- contact/availability;
- recent evidence;
- target role.

Completeness отображается кандидату и может использоваться как подсказка, но MUST NOT напрямую повышать Match Score.

### 17.3 Статусы skill

- `claimed` — только self-claim;
- `supported` — есть дополнительное evidence;
- `verified` — источник/ownership проверен;
- `assessed` — подтверждён platform assessment;
- `disputed` — кандидат оспорил результат;
- `stale` — evidence устарело.

---

# Часть V. Vacancy Matching

## 18. Requirement model

Каждое vacancy requirement содержит:

- skill_id или constraint type;
- requirement_type;
- target_level;
- weight;
- hard_filter;
- minimum_confidence;
- accepted_evidence_types;
- explanation;
- display_order.

### 18.1 Weight rules

- сумма весов must-have внутри категории нормализуется;
- сумма весов nice-to-have нормализуется отдельно;
- employer может выбирать пресеты;
- employer не может задать отрицательный вес;
- employer не может использовать protected attribute;
- система предупреждает о нереалистичных junior requirements.

## 19. Eligibility

Eligibility проверяет только жёсткие constraints:

- legal work authorization, если законно и необходимо;
- location/remote compatibility;
- availability;
- required language;
- mandatory schedule;
- explicit hard skill only when employer подтверждает его как реальный hard filter.

Результаты:

- `eligible`;
- `conditionally_eligible`;
- `not_eligible`;
- `unknown`.

Unknown не равен not eligible.

## 20. Match Score

### 20.1 Базовая формула v1

```text
base_match =
    0.35 * must_have_coverage
  + 0.15 * nice_to_have_coverage
  + 0.20 * evidence_strength
  + 0.15 * project_relevance
  + 0.10 * recency_and_learning_velocity
  + 0.05 * role_constraints_fit
```

Итог:

```text
match_score = clamp(base_match - penalties, 0, 100)
```

### 20.2 Компоненты

**Must-have coverage** учитывает:

- наличие skill;
- target level;
- candidate skill score;
- confidence;
- requirement weight.

**Nice-to-have coverage** является бонусной частью и не должна компенсировать полностью отсутствие критического must-have.

**Evidence strength** показывает качество подтверждений именно для требований этой вакансии.

**Project relevance** определяется по совпадению технологий, задач и сложности проектов с контекстом роли.

**Recency and learning velocity** учитывает свежесть evidence и скорость появления новых подтверждений, но не должен дискриминировать людей с перерывами.

**Role constraints fit** учитывает только законные операционные ограничения.

### 20.3 Hard must-have cap

Если отсутствует обязательный hard must-have и работодатель явно подтвердил hard filter:

```text
match_score <= 59
```

В интерфейсе должно быть написано, какой критерий вызвал cap.

### 20.4 Penalties

| Причина | Диапазон |
|---|---:|
| Противоречивые данные | 0…-15 |
| Низкая проверяемость критического claim | 0…-10 |
| Ownership unresolved | 0…-10 |
| Подтверждённый spam/fraud pattern | 0…-20 |

Penalty MUST:

- иметь reason code;
- быть видимым в explanation;
- не основываться на защищённых характеристиках;
- быть оспоримым;
- сохраняться в audit trail.

### 20.5 Match bands

- 85–100 — strong match;
- 70–84 — promising match;
- 55–69 — partial match;
- 0–54 — significant gaps.

Bands не являются решением о найме.

## 21. Match Confidence

Match Confidence отражает качество данных для конкретной вакансии.

```text
match_confidence = weighted_average(
  confidence_of_required_skills,
  requirement_coverage,
  source_diversity,
  vacancy_definition_quality,
  extraction_certainty
)
```

Высокий Match при низком Confidence должен отображаться как требующий дополнительной проверки.

Пример:

- Match 82, Confidence 38 → перспективно, но мало подтверждений;
- Match 78, Confidence 91 → немного ниже score, но результат устойчивее.

## 22. Explainability

Каждый match result должен включать:

- top strengths;
- critical gaps;
- matched requirements;
- unmatched requirements;
- score contributions;
- confidence reasons;
- penalties;
- next best evidence;
- scoring version.

Пример:

```text
Match 82 / Confidence 71

Strengths
+ Python: resume + GitHub + project
+ FastAPI: confirmed in two repositories
+ PostgreSQL: confirmed in one relevant project

Gaps
- Docker: claimed but not confirmed
- Testing: insufficient verifiable evidence

Next action
Add tests and Docker setup to one existing project or complete the recommended assessment.
```

AI может превратить deterministic breakdown в читаемый текст, но не может изменить значения.

## 23. Skill Gaps

Gap содержит:

- requirement;
- current state;
- target state;
- severity;
- evidence missing vs skill missing;
- recommended action;
- estimated effort band;
- expected score influence band;
- verification method.

Критически важно различать:

- **skill gap** — навык действительно не обнаружен;
- **evidence gap** — навык заявлен, но плохо подтверждён;
- **confidence gap** — данные противоречивы или устарели;
- **constraint gap** — несовместимость по операционному требованию.

---

# Часть VI. AI и автоматизация

## 24. Разрешённая роль AI

AI MAY:

- извлекать структурированные данные из резюме;
- нормализовать названия skills;
- классифицировать project context;
- определять предполагаемую релевантность evidence;
- предлагать структуру вакансии;
- писать объяснение на основе готового breakdown;
- проводить rubric-based review;
- формировать roadmap в заданных пределах;
- обнаруживать противоречия для human review.

AI MUST NOT:

- вычислять финальный Match Score;
- менять веса;
- отклонять кандидата;
- присваивать защищённые характеристики;
- делать медицинские, психологические или личностные выводы;
- использовать лицо, возраст, пол, этничность, религию или семейное положение;
- придумывать отсутствующие evidence;
- скрывать uncertainty;
- исполнять пользовательский код.

## 25. AI Orchestrator

В системе существует один AI Orchestrator с provider abstraction.

Prompt families:

1. resume extraction;
2. vacancy extraction;
3. evidence classification;
4. assessment rubric review;
5. explanation and roadmap.

Каждый AI result содержит:

- prompt family;
- prompt version;
- provider;
- model;
- input hash;
- output schema version;
- raw output reference;
- validated output;
- latency;
- token usage;
- estimated cost;
- status;
- created_at.

## 26. Structured output

Все AI outputs должны валидироваться Pydantic schema.

При ошибке:

1. один bounded repair attempt;
2. при повторной ошибке job = failed;
3. UI показывает retry;
4. невалидный output не попадает в scoring.

## 27. Demo mode

Hackathon MVP MUST работать без внешнего LLM.

Demo mode:

- использует fixtures;
- возвращает детерминированные результаты;
- соблюдает те же schemas;
- проходит тот же downstream pipeline;
- явно маркируется в технической конфигурации, но не ломает UX demo.

## 28. Cost control

Система должна фиксировать AI usage и поддерживать:

- model routing;
- maximum input length;
- maximum output tokens;
- caching по input hash;
- deduplication jobs;
- per-organization limits;
- monthly budget alerts;
- fallback to cheaper model for low-risk extraction;
- manual disable switch.

---

# Часть VII. Монетизация

## 29. Основная модель

Основная модель BeyondResume — **hybrid B2B SaaS**:

```text
Base subscription
+ included monthly analyses
+ usage overage
+ annual contracts
+ optional API / integrations / enterprise add-ons
```

Почему:

- subscription монетизирует workspace, collaboration, vacancies, history и analytics;
- usage monetizes переменную ценность и compute;
- annual contracts улучшают retention и cash flow;
- overage защищает gross margin;
- API и white-label создают expansion revenue.

## 30. Кто платит

### 30.1 Основной плательщик

Организация-работодатель.

Она платит за:

- сокращение screening time;
- более качественный shortlist;
- стандартизацию junior evaluation;
- collaboration;
- auditability;
- интеграцию с hiring workflow.

### 30.2 Кандидат

Основной candidate experience остаётся бесплатным.

Free Candidate MUST включать:

- профиль;
- одно активное резюме;
- базовый Skill Passport;
- просмотр match;
- gaps;
- базовый roadmap;
- управление данными;
- applications.

Платные candidate services MAY включать:

- one-off deep review;
- расширенный карьерный отчёт;
- interview preparation pack;
- дополнительные assessments;
- экспертную проверку профиля.

Платные функции кандидата не должны создавать pay-to-rank или повышать employer score только за оплату.

## 31. Рекомендуемые тарифы

Цены являются стартовой гипотезой и должны быть подтверждены customer interviews и pilot data.

### 31.1 Sandbox / Trial

**Цена:** $0  
**Срок:** 14 дней или design-partner period  
**Лимиты:**

- 1 active vacancy;
- 50 candidate analyses;
- 2 seats;
- basic Skill Passport and Match;
- no API;
- no bulk export;
- no advanced analytics.

### 31.2 Starter

**Цена:** $199/month или $1,990/year.  
**ЦА:** startup и small software team.

Включено:

- 3 active vacancies;
- 300 candidate analyses/month;
- 3 seats;
- Skill Passport;
- Match + Confidence;
- explainability;
- shortlist pipeline;
- CSV export limited;
- email support.

Overage: $1.00 per additional analysis.

### 31.3 Growth

**Цена:** $749/month или $7,490/year.  
**ЦА:** mid-market hiring team.

Включено:

- 15 active vacancies;
- 2,000 analyses/month;
- 10 seats;
- advanced filters;
- team notes;
- analytics;
- custom requirement presets;
- webhooks;
- ATS export;
- priority support.

Overage: $0.75 per additional analysis.

### 31.4 Agency

**Цена:** $1,499/month или $14,990/year.  
**ЦА:** recruiting/staffing agencies.

Включено:

- 30 active client vacancies;
- 3,000 analyses/month;
- 10 seats;
- client workspaces;
- branded candidate reports;
- reusable vacancy templates;
- higher export limits;
- agency analytics.

Overage: $0.65 per additional analysis.

### 31.5 Scale

**Цена:** $2,499/month или $24,990/year.  
**ЦА:** high-volume hiring operations.

Включено:

- 50 active vacancies;
- 10,000 analyses/month;
- 30 seats;
- API access with limit;
- SSO add-on readiness;
- custom retention;
- audit export;
- dedicated success contact.

Overage: $0.50 per additional analysis.

### 31.6 Enterprise

**Цена:** от $42,000/year.  
**ЦА:** banks, telecom, large technology employers, regulated companies.

Включено по договору:

- custom volumes;
- SSO/SAML;
- SCIM;
- regional data hosting roadmap;
- DPA/SCC;
- security review;
- SLA;
- custom audit retention;
- advanced integrations;
- bias audit pack;
- dedicated support;
- optional private model/provider configuration.

## 32. Billing unit

Основная usage unit: **Candidate Analysis Unit**.

Одна unit списывается, когда система создаёт новый существенный analysis result для пары:

- candidate profile snapshot;
- vacancy version или general passport generation;
- organization.

Не списывается повторно, если:

- тот же snapshot уже анализировался;
- запрос повторён из-за UI retry;
- job failed до создания валидного result;
- результат взят из permitted cache.

Дополнительные billable units в будущем:

- deep repository analysis;
- assessment review;
- API batch processing;
- identity verification;
- premium report.

## 33. Usage metering

Каждое usage event содержит:

- organization_id;
- subscription_id;
- event_type;
- quantity;
- unit_price;
- source entity;
- idempotency key;
- occurred_at;
- billing_period;
- status;
- cost estimate;
- metadata.

Usage MUST быть идемпотентным.

## 34. Plan enforcement

### 34.1 Soft limits

При достижении 80%:

- уведомление Company Admin;
- banner в billing;
- прогноз overage.

При 100%:

- если overage enabled — обработка продолжается и usage тарифицируется;
- если overage disabled — новые billable analyses блокируются, но существующие данные доступны;
- системные retry не блокируются;
- кандидат не должен терять уже рассчитанный результат.

### 34.2 Active vacancy limit

Новая публикация блокируется, если active vacancy limit исчерпан.

Draft вакансии могут создаваться сверх лимита, но не публиковаться.

### 34.3 Seat limit

Company Admin не может активировать нового member сверх seat limit.

При downgrade существующие пользователи не удаляются автоматически: лишние seats переводятся в suspended по явному выбору админа до следующего billing period.

## 35. Subscription lifecycle

Статусы:

- `trialing`;
- `active`;
- `past_due`;
- `grace_period`;
- `paused`;
- `cancel_at_period_end`;
- `cancelled`;
- `expired`.

### 35.1 Failed payment

Рекомендуемая политика:

1. payment failed → `past_due`;
2. 7-day grace period;
3. в grace доступ сохраняется, но новые overage-heavy actions MAY быть ограничены;
4. после grace → `paused`;
5. данные доступны read-only;
6. восстановление после оплаты;
7. удаление данных не происходит автоматически сразу после cancellation.

### 35.2 Cancellation

- cancellation effective at period end;
- данные экспортируемы;
- read-only window не менее 30 дней для self-serve;
- enterprise — по договору;
- candidate data retention определяется consent и employer legal basis, а не только подпиской.

### 35.3 Annual discount

Рекомендуемый discount: 15–18%.

Annual contract должен быть основным предложением после pilot.

## 36. Candidate premium

Не входит в основной revenue forecast.

Возможные SKU:

- Deep Profile Review — $29 one-off;
- Advanced Career Report — $19;
- Assessment Pack — $15–$39;
- Human Expert Review — marketplace price;
- Interview Readiness Pack — $29.

Запрещено:

- продавать повышение Match Score;
- скрывать основные gaps за paywall;
- давать employer badge «paid candidate»;
- ставить платных кандидатов выше.

## 37. API monetization

Post-MVP:

- minimum commit $1,000–$3,000/month;
- usage tiers;
- separate rate limits;
- API keys per organization;
- signed webhooks;
- SLA by plan;
- audit and cost dashboard.

## 38. White-label

Post-MVP:

- setup fee $5,000–$15,000;
- monthly license;
- usage overage;
- limited branding configuration;
- no custom fork by default;
- all scoring changes remain versioned platform configuration.

## 39. Education partnerships

Партнёрства с universities и bootcamps могут давать:

- cohort Skill Passport;
- graduate readiness analytics;
- employer showcase;
- gap-to-course flow;
- referral revenue.

Revenue model:

- annual institutional license;
- per-student fee;
- employer-sponsored cohorts;
- referral share.

Рекомендации курсов MUST быть явно маркированы как sponsored, если есть коммерческая связь.

---

# Часть VIII. Unit economics и финансовая дисциплина

## 40. Основные допущения

Все значения в этой главе — управленческие гипотезы, а не гарантированный прогноз.

Целевые показатели:

- gross margin: 80%+;
- LTV/CAC: >3;
- CAC payback: <10–12 months;
- annual plan share: >50% после первого года продаж;
- pilot-to-paid conversion: >18%;
- SMB monthly logo churn: <1.5%;
- mid-market monthly logo churn: <0.8%.

## 41. Себестоимость одной обработки

Себестоимость Candidate Analysis Unit состоит из:

- document parsing;
- storage;
- database operations;
- GitHub/API calls;
- LLM input/output;
- background compute;
- monitoring;
- support allocation.

Целевой variable COGS:

| Этап | Целевой диапазон |
|---|---:|
| Parsing and compute | $0.01–$0.05 |
| Storage and DB | $0.005–$0.02 |
| GitHub/API | $0.00–$0.03 |
| LLM extraction/explanation | $0.05–$0.30 |
| Monitoring/support allocation | $0.02–$0.10 |
| **Total target** | **$0.10–$0.50** |

При цене overage $0.50–$1.00 unit economics сохраняется только при model routing и caching.

## 42. Cost controls as product requirements

Commercial MVP MUST иметь:

- token and cost logging;
- organization usage dashboard;
- global cost dashboard;
- alerts при аномальном usage;
- job deduplication;
- cache hit rate;
- per-feature COGS;
- retry limits;
- protection от бесконечных cycles;
- budget cap на provider.

## 43. Реалистичный operating model

### 43.1 Lean founder/hackathon stage

Ожидаемые месячные расходы без рыночных зарплат founders:

- cloud and database: $50–$300;
- LLM/API: $50–$500;
- domain/email/tools: $50–$200;
- legal/accounting: variable;
- marketing tests: $100–$1,000.

### 43.2 Funded commercial stage

Основной cost driver — команда и go-to-market, а не storage.

Типичная структура:

- engineering/product;
- sales;
- customer success;
- security/legal;
- infrastructure and AI COGS;
- marketing.

## 44. ROI calculator для работодателя

Сайт SHOULD иметь employer ROI calculator.

Input:

- applications per vacancy;
- minutes per manual screen;
- recruiter hourly cost;
- vacancies per month;
- estimated screening reduction.

Output:

```text
manual_screening_cost = applications * minutes / 60 * hourly_cost
monthly_savings = manual_cost * vacancies * reduction_rate
estimated_roi = (monthly_savings - subscription_price) / subscription_price
```

Результат маркируется как estimate.

## 45. North Star Metric

**Verified recruiter screening time saved per paid organization.**

Supporting metrics:

- candidates analyzed;
- explanation open rate;
- shortlist precision;
- time to first useful shortlist;
- request-more-evidence rate;
- recruiter override rate;
- paid retention;
- expansion MRR.

---

# Часть IX. Интерфейс сайта

## 46. Общая навигация

### 46.1 Candidate navigation

- Dashboard;
- Skill Passport;
- Evidence;
- Vacancies;
- Applications;
- Assessments;
- Roadmap;
- Settings.

### 46.2 Employer navigation

- Dashboard;
- Vacancies;
- Candidates;
- Pipeline;
- Analytics;
- Team;
- Integrations;
- Billing;
- Organization Settings.

## 47. Public pages

MUST:

- landing page;
- product page;
- pricing page;
- candidate page;
- employer page;
- login;
- registration;
- privacy;
- terms.

SHOULD:

- security page;
- methodology page;
- explainable scoring page;
- demo request;
- ROI calculator.

## 48. Candidate Dashboard

Содержит:

- onboarding progress;
- latest Skill Passport summary;
- completeness;
- top skills;
- low-confidence skills;
- recommended next action;
- recent applications;
- analysis status;
- profile visibility.

Primary CTA зависит от состояния:

- Complete profile;
- Upload resume;
- Add GitHub;
- Analyze profile;
- View Skill Passport;
- Complete assessment.

## 49. Skill Passport page

Header:

- candidate summary;
- target role;
- passport version;
- generated date;
- completeness;
- overall confidence.

Skill card:

- skill name;
- level;
- score;
- confidence;
- status;
- evidence count;
- freshness;
- expandable evidence list.

UI MUST различать:

- claimed;
- supported;
- verified;
- assessed;
- stale;
- disputed.

## 50. Vacancy page for candidate

Содержит:

- company;
- title;
- description;
- requirements;
- employment details;
- transparency note;
- Apply CTA;
- Match block, если доступен.

Match block:

- Match Score;
- Confidence;
- eligibility;
- strengths;
- gaps;
- next action;
- scoring version details in expandable section.

## 51. Employer vacancy list

Колонки:

- title;
- status;
- active applicants;
- analyses used;
- shortlist count;
- owner;
- updated_at.

Actions:

- create;
- duplicate;
- edit;
- publish;
- pause;
- close;
- archive.

## 52. Employer candidate ranking

Table/card view:

- candidate display name;
- target role;
- Match;
- Confidence;
- top evidence;
- top gap;
- stage;
- flags;
- last activity.

Filters:

- stage;
- match range;
- confidence range;
- skill;
- evidence status;
- eligibility;
- updated date.

Нельзя добавлять фильтры по защищённым характеристикам.

## 53. Candidate detail for employer

Sections:

- Match summary;
- Confidence explanation;
- Requirements breakdown;
- Skill Passport excerpt;
- Evidence timeline;
- Projects;
- Assessments;
- Application history;
- Internal notes;
- Human actions.

Primary actions:

- shortlist;
- request evidence;
- invite;
- move stage;
- reject.

## 54. Billing page

Company Admin видит:

- current plan;
- renewal date;
- included limits;
- current usage;
- projected overage;
- invoices;
- payment method;
- upgrade/downgrade;
- annual savings;
- usage by vacancy;
- usage by feature.

## 55. Pricing page

Pricing page должна:

- объяснять, что считается analysis;
- показывать included volume;
- показывать overage;
- не скрывать базовые ограничения;
- давать monthly/annual toggle;
- содержать CTA Start trial / Book demo;
- отдельно показывать candidate free plan;
- указывать, что Enterprise custom.

## 56. Состояния UI

Каждый async flow MUST иметь:

- idle;
- uploading;
- queued;
- processing;
- success;
- failed;
- retrying;
- cancelled/expired при необходимости.

Ошибки должны быть user-facing, без stack traces.

---

# Часть X. Техническая архитектура

## 57. Архитектурный стиль

Hackathon MVP и Commercial MVP используют modular monolith.

Стек:

- Frontend: Next.js App Router + TypeScript + Tailwind CSS;
- Backend: FastAPI + Python 3.12;
- Validation: Pydantic v2;
- ORM: SQLAlchemy 2;
- Migrations: Alembic;
- Database: PostgreSQL 16;
- Deployment: Docker Compose для MVP;
- Object storage: local volume в Hackathon MVP, S3-compatible в Commercial MVP;
- Background processing: FastAPI BackgroundTasks + jobs table в Hackathon MVP;
- Production queue MAY быть добавлена позже при фактической необходимости.

## 58. Модули backend

```text
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
  billing/
  analytics/
```

Доменные модули:

- auth;
- users;
- candidates;
- organizations;
- memberships;
- resumes;
- jobs;
- evidence;
- skills;
- passports;
- vacancies;
- applications;
- matching;
- assessments;
- roadmaps;
- invitations;
- subscriptions;
- usage;
- audit.

## 59. Frontend architecture

- Server-rendered shell;
- client components для interactive forms;
- TanStack Query для API state и polling;
- Zod для client validation;
- no business formulas in frontend;
- no direct LLM calls;
- route-level role guards;
- feature modules по доменам;
- i18n-ready text keys.

## 60. Background jobs

### 60.1 Job types

- resume_parse;
- profile_analysis;
- github_scan;
- passport_generation;
- vacancy_normalization;
- match_calculation;
- assessment_review;
- roadmap_generation;
- export_generation;
- webhook_delivery.

### 60.2 Job statuses

- `pending`;
- `running`;
- `completed`;
- `failed`;
- `cancelled`;
- `expired`.

### 60.3 Job rules

- job имеет owner/context;
- status transitions валидируются;
- retry_count ограничен;
- ошибки типизированы;
- payload не должен содержать secrets;
- result reference хранится отдельно;
- user видит безопасный error message;
- admin видит technical error code;
- duplicate jobs предотвращаются idempotency key.

Для `resume_parse` текущего MVP Job относится к Resume и использует lifecycle
`pending → running → completed|failed`. Повторный запуск возвращает существующий активный Job
либо создаёт новую попытку только после failed Job в соответствии с правилами retry. Результат
plain-text parsing хранится внутренне и не является публичным Job result.

## 61. API conventions

Base path: `/api/v1`.

Требования:

- JSON snake_case;
- UTC timestamps ISO 8601;
- UUID identifiers;
- consistent error schema;
- pagination;
- idempotency keys для billable/write operations;
- role and tenant authorization;
- OpenAPI documentation;
- request correlation id.

Error schema:

```json
{
  "error": {
    "code": "string_code",
    "message": "User-facing message",
    "details": {},
    "request_id": "uuid"
  }
}
```

## 62. Основные API группы

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Candidate

- `GET /candidate/profile`
- `PATCH /candidate/profile`
- `PATCH /candidate/visibility`

### Resume

- `POST /candidate/resumes`
- `GET /candidate/resumes`
- `GET /candidate/resumes/{id}`
- `POST /candidate/resumes/{id}/parse`

`POST /candidate/resumes/{id}/parse` запускает только plain-text parsing Job и не возвращает
извлечённый текст. Отдельного endpoint для parsing result нет.

### Jobs

- `GET /jobs/{id}`

`GET /jobs/{id}` является единственным публичным polling endpoint для Resume processing.

### Evidence

- `GET /candidate/evidence`
- `POST /candidate/evidence`
- `DELETE /candidate/evidence/{id}`
- `POST /candidate/evidence/{id}/dispute`

### Analysis and Passport

- `POST /candidate/analysis`
- `GET /candidate/passports`
- `GET /candidate/passports/latest`
- `GET /candidate/passports/{id}`

### Organizations

- `POST /organizations`
- `GET /organizations/{id}`
- `PATCH /organizations/{id}`
- `GET /organizations/{id}/members`
- `POST /organizations/{id}/invitations`

### Vacancies

- `POST /organizations/{id}/vacancies`
- `GET /organizations/{id}/vacancies`
- `GET /vacancies/{id}`
- `PATCH /vacancies/{id}`
- `POST /vacancies/{id}/publish`
- `POST /vacancies/{id}/pause`
- `POST /vacancies/{id}/close`

### Matching

- `POST /vacancies/{id}/match`
- `GET /vacancies/{id}/matches`
- `GET /matches/{id}`

### Applications

- `POST /vacancies/{id}/applications`
- `GET /candidate/applications`
- `GET /vacancies/{id}/applications`
- `PATCH /applications/{id}/stage`
- `POST /applications/{id}/withdraw`

### Assessments

- `POST /applications/{id}/assessment`
- `GET /assessments/{id}`
- `POST /assessments/{id}/submissions`

### Billing

- `GET /organizations/{id}/subscription`
- `GET /organizations/{id}/usage`
- `POST /organizations/{id}/checkout`
- `POST /billing/webhooks/provider`

## 63. Database entities

### Existing baseline

- users;
- candidate_profiles;
- employer_profiles;
- resumes.

### Required next entities

- jobs;
- organizations;
- organization_memberships;
- organization_invitations;
- skills;
- skill_aliases;
- evidence_units;
- evidence_skill_links;
- profile_snapshots;
- skill_passports;
- passport_skills;
- vacancies;
- vacancy_requirements;
- vacancy_versions;
- applications;
- application_events;
- match_results;
- match_factors;
- assessments;
- assessment_submissions;
- assessment_results;
- roadmaps;
- roadmap_steps;
- recruiter_invitations;
- subscriptions;
- plan_definitions;
- usage_events;
- invoices references;
- ai_runs;
- audit_events.

## 64. Billing data model

### PlanDefinition

- code;
- name;
- billing_interval support;
- price;
- currency;
- active_vacancy_limit;
- analysis_limit;
- seat_limit;
- overage_enabled;
- overage_unit_price;
- features JSON;
- version;
- active_from/to.

### Subscription

- organization_id;
- provider_customer_id;
- provider_subscription_id;
- plan_definition_id;
- status;
- period_start;
- period_end;
- cancel_at_period_end;
- trial_end;
- overage_enabled;
- created_at;
- updated_at.

### UsageEvent

- organization_id;
- subscription_id;
- event_type;
- quantity;
- unit_price_snapshot;
- idempotency_key unique;
- source_type;
- source_id;
- billing_period_start;
- occurred_at;
- status.

## 65. Audit events

Audit event нужен для:

- scoring version changes;
- employer stage/rejection actions;
- evidence dispute;
- admin override;
- subscription changes;
- exports;
- API key changes;
- privacy actions;
- organization membership changes.

---

# Часть XI. Безопасность, privacy и fairness

## 66. Authentication

- Argon2id password hashing;
- JWT access tokens;
- refresh strategy в Commercial MVP;
- account status check;
- rate limiting;
- email verification SHOULD;
- MFA SHOULD для Company Admin;
- SSO post-MVP.

## 67. Authorization

Каждый запрос проверяет:

- authenticated user;
- role;
- organization membership;
- permission;
- ownership/context;
- entity visibility.

Frontend guard не заменяет backend authorization.

## 68. Protected attributes

Scoring MUST NOT использовать:

- race/ethnicity;
- gender/sex;
- age/date of birth;
- religion;
- disability;
- family status;
- pregnancy;
- political views;
- photograph/face;
- name-based demographic inference.

Необходимые accessibility accommodations обрабатываются отдельно и не снижают score.

## 69. Human review

- no auto-reject by default;
- adverse action требует human confirmation;
- recruiter может override ranking;
- override reason логируется;
- кандидат может оспорить evidence;
- score является decision support.

## 70. Privacy rights

Candidate должен иметь возможность:

- получить экспорт своих данных;
- удалить аккаунт;
- удалить отдельный evidence source;
- отозвать discovery visibility;
- исправить данные;
- увидеть основные причины scoring;
- оспорить результат.

## 71. Retention

Рекомендуемый baseline:

- raw resume file — пока нужен для профиля или до удаления пользователем;
- failed upload temp files — немедленное удаление;
- AI raw payload — ограниченный срок;
- application data — по employer policy и legal basis;
- audit events — дольше основных operational records;
- cancelled B2B workspace — read-only export window, затем policy-based deletion.

Конкретные сроки должны быть утверждены перед Commercial MVP.

## 72. Security controls

- file size/type limits;
- safe filenames;
- antivirus/malware scanning SHOULD commercial;
- encrypted transport;
- encrypted storage commercial;
- secrets only through environment/secret manager;
- no secrets in logs;
- dependency scanning;
- backup and restore;
- audit logs;
- request rate limits;
- webhook signature verification;
- upload access controls;
- SSRF protection для URL scanning.

---

# Часть XII. Analytics и продуктовые метрики

## 73. Event taxonomy

Candidate events:

- registered;
- profile_completed;
- resume_uploaded;
- resume_parsed;
- evidence_added;
- analysis_started/completed/failed;
- passport_viewed;
- vacancy_viewed;
- match_viewed;
- application_submitted;
- assessment_submitted;
- roadmap_step_completed.

Employer events:

- organization_created;
- trial_started;
- vacancy_created/published;
- candidate_analyzed;
- explanation_opened;
- shortlisted;
- evidence_requested;
- invited;
- rejected;
- hired;
- checkout_started/completed;
- plan_upgraded/downgraded;
- limit_reached;
- overage_incurred.

## 74. Product KPIs

### Activation

- candidate time to first passport < 3 minutes after valid inputs;
- employer time to first ranked candidate < 10 minutes;
- passport completion > 65%;
- trial organization publishes vacancy > 40%.

### Value

- screening time reduction > 40%;
- explanation open rate > 60%;
- recruiter useful-match acceptance > 70%;
- shortlist precision uplift target +20% vs client baseline.

### Revenue

- pilot-to-paid > 18%;
- gross margin > 80%;
- CAC payback < 10–12 months;
- LTV/CAC > 3;
- expansion revenue > 15% by end of year 2.

### Reliability

- parsing success > 95% for supported valid files;
- AI schema validation > 98% after bounded repair;
- job success > 97% excluding invalid input;
- no duplicate billing events.

### Fairness and trust

- 100% adverse actions human-confirmed;
- evidence dispute response SLA;
- fairness monitoring by permitted aggregate cohorts;
- zero protected attributes in scoring features.

---

# Часть XIII. Scope и roadmap

## 75. Уже реализованный baseline

На дату версии документа реализованы:

- project bootstrap;
- PostgreSQL foundation;
- JWT authentication;
- candidate profile API;
- resume upload;
- resume text parsing service;
- tests and quality gates for these stages.

Эта реализация должна сохраняться и развиваться без необоснованной переработки.

## 76. Hackathon MVP MUST HAVE

1. Candidate auth and profile.
2. Resume upload and parsing.
3. Background jobs and polling.
4. One GitHub repository source.
5. Deterministic GitHub scan.
6. AI/demo extraction.
7. Skill Passport v1.
8. One structured vacancy.
9. Deterministic Match Score and Confidence.
10. Gap explanation.
11. One assessment lifecycle.
12. Roadmap 3–5 steps.
13. Employer ranking inside own vacancy.
14. Invitation action.
15. End-to-end frontend demo.
16. Docker Compose startup.

Billing payment integration не обязана быть рабочей в Hackathon MVP, но pricing и plan model должны быть отражены в архитектуре без блокировки core flow.

## 77. Commercial MVP MUST HAVE

1. Organizations and memberships.
2. Multi-tenant authorization.
3. Subscription and usage metering.
4. Trial and plan enforcement.
5. Multiple vacancies.
6. Recruiter collaboration.
7. Application pipeline.
8. Candidate visibility controls.
9. Audit events.
10. Privacy export/delete.
11. S3-compatible storage.
12. Monitoring and cost dashboard.
13. Payment provider integration.
14. Production email.
15. Legal pages and consent records.
16. Basic ATS export/webhook.
17. Security hardening.

## 78. Post-MVP

- agency multi-client workspace;
- public API;
- white-label;
- SSO/SCIM;
- university cohorts;
- certificate issuer integrations;
- GitHub profile-wide analysis;
- external assessments;
- human reviewer marketplace;
- advanced fraud signals;
- multilingual ontology;
- mobile application;
- enterprise bias audit tooling.

## 79. Запрещённое scope expansion до завершения MVP

- полноценная ATS replacement;
- social network;
- messaging platform;
- video interviews;
- payroll;
- employee HRIS;
- automatic code execution sandbox;
- personality analysis;
- face/voice analysis;
- generative cover-letter marketplace;
- blockchain credentials.

---

# Часть XIV. Этапы дальнейшей разработки

## 80. Рекомендуемая последовательность

### Stage 6B — Resume Parsing Job

- jobs table;
- BackgroundTasks trigger;
- pending → running → completed/failed;
- safe PDF/DOCX plain-text extraction into internal `Resume.extracted_text`;
- `Resume: uploaded → parsed|failed` without a `parsing` status;
- `GET /api/v1/jobs/{job_id}`;
- upload response returns job reference;
- tests for idempotency and failures.

Stage 6B не включает structured extraction, contacts, education, projects, skills, Evidence,
Skill Passport, AI analysis или matching. Эти функции относятся к последующим отдельным модулям.

### Stage 7 — GitHub Evidence

- repository model;
- URL validation;
- safe GitHub integration;
- deterministic scan;
- repository snapshot;
- evidence extraction without AI scoring.

### Stage 8 — Profile Analysis Orchestrator

- profile snapshot;
- AI adapter;
- structured extraction;
- demo fixtures;
- job lifecycle;
- cost metadata.

### Stage 9 — Evidence Graph and Skill Passport

- skill ontology;
- evidence units;
- skill claims;
- deterministic skill score;
- passport versions;
- candidate API.

### Stage 10 — Vacancy

- employer organization simplification;
- vacancy and requirements;
- AI-assisted normalization;
- confirmation and publish rules.

### Stage 11 — Matching

- deterministic factors;
- confidence;
- penalties;
- explanation data;
- ranking API.

### Stage 12 — Assessments

- assignment;
- submission;
- deterministic checks;
- rubric AI review;
- recalculation.

### Stage 13 — Roadmap and Invitation

- gap actions;
- roadmap;
- employer invitation;
- application events.

### Stage 14 — Frontend End-to-End

- candidate flow;
- employer flow;
- polling;
- errors;
- demo data;
- responsive UI.

### Stage 15 — Commercial Foundation

- organizations;
- memberships;
- subscription;
- usage;
- pricing page;
- billing dashboard;
- provider integration.

---

# Часть XV. Acceptance criteria

## 81. Product acceptance

Система считается соответствующей core product logic, если:

- кандидат получает Skill Passport на основе evidence;
- self-claim визуально и математически отличается от verified evidence;
- Match и Confidence отображаются отдельно;
- score раскрывается до факторов;
- gap различает missing skill и missing evidence;
- employer принимает финальное решение сам;
- candidate может исправить или оспорить данные;
- AI не вычисляет итоговые числа.

## 82. Commercial acceptance

Commercial MVP считается готовым к первым платным pilot, если:

- tenant isolation протестирован;
- usage считается идемпотентно;
- plan limits работают;
- trial lifecycle работает;
- billing failure не удаляет данные;
- Company Admin видит usage;
- variable COGS измеряется;
- privacy actions реализованы;
- audit trail существует;
- customer can measure time saved.

## 83. Technical quality gates

Backend:

- pytest passing;
- Ruff passing;
- mypy strict passing;
- Alembic migration tests;
- PostgreSQL integration smoke test;
- no unhandled file handles;
- no business formulas in routers.

Frontend:

- typecheck passing;
- lint passing;
- critical flow tests;
- loading/error/empty states;
- accessibility baseline;
- no scoring logic.

Repository:

- no secrets;
- clean git status before commit;
- atomic commits;
- documentation updated with behavior changes;
- Docker Compose smoke test.

---

# Часть XVI. Решения, требующие отдельного утверждения

До Commercial MVP необходимо отдельно утвердить:

1. точный первый рынок и валюта billing;
2. payment provider;
3. юридическое лицо и data controller roles;
4. retention periods;
5. production LLM provider/model routing;
6. окончательные тарифы после 20+ interviews;
7. exact overage definition;
8. fairness evaluation methodology;
9. GitHub data usage policy;
10. public discovery policy;
11. assessment ownership and anti-cheat rules;
12. enterprise hosting strategy.

---


# Часть XVII. Жёсткое ограничение: продукт должен быть готов за 5 дней

## 84. Главный delivery-инвариант

BeyondResume MUST быть подготовлен к демонстрации за пять календарных дней. Это ограничение имеет более высокий приоритет, чем полнота Commercial MVP и Post-MVP.

За пять дней команда обязана получить не набор разрозненных экранов, а один полностью работающий end-to-end сценарий:

1. кандидат регистрируется;
2. заполняет базовый профиль;
3. загружает резюме;
4. система извлекает текст и навыки;
5. кандидат добавляет один GitHub-репозиторий;
6. система создаёт evidence и Skill Passport;
7. работодатель создаёт структурированную вакансию;
8. система рассчитывает Match Score и Confidence Score;
9. работодатель видит объяснимый рейтинг кандидатов;
10. работодатель открывает карточку кандидата и отправляет приглашение;
11. кандидат видит приглашение и gaps/roadmap.

Любая функция, которая не улучшает этот демонстрационный путь, MUST быть перенесена в Commercial MVP или Post-MVP.

## 85. Definition of Done пятидневного MVP

Hackathon MVP считается завершённым только при одновременном выполнении условий:

- проект запускается одной документированной командой Docker Compose;
- миграции применяются на чистой базе;
- backend health endpoint отвечает успешно;
- frontend открывается без ручной правки конфигурации;
- регистрация и вход работают;
- кандидат может создать и изменить профиль;
- PDF/DOCX resume upload проходит валидацию;
- parsing job имеет видимые статусы;
- хотя бы один GitHub repository анализируется детерминированно или через зафиксированный demo fixture;
- Skill Passport строится из реальных сохранённых данных;
- вакансия создаётся и публикуется;
- Match Score рассчитывается backend, а не LLM;
- объяснение score содержит подтверждённые навыки, gaps и confidence;
- employer ranking отображает минимум трёх demo-кандидатов либо одного реального и demo fixtures;
- приглашение создаёт сохранённое событие в базе;
- критические ошибки показываются пользователю понятным текстом;
- ключевой сценарий покрыт smoke/integration tests;
- demo можно повторить минимум три раза без ручного восстановления базы.

Красивый интерфейс без сохранения данных, захардкоженный score без backend-расчёта или набор несвязанных страниц не считается готовым MVP.

## 86. Разрешённые упрощения Hackathon MVP

В целях срока разрешено:

- использовать BackgroundTasks вместо Celery;
- использовать локальное файловое хранилище;
- использовать polling вместо WebSocket;
- поддерживать один GitHub repository на кандидата;
- использовать зафиксированную skill ontology v1;
- использовать demo AI adapter при отсутствии ключа провайдера;
- иметь одну организацию на employer account;
- поддерживать роли Candidate и Employer без полной team administration;
- отображать тарифы без реального списания денег;
- использовать seed/demo data;
- делать invitation внутри продукта без отправки email;
- применять английские canonical skill names при русском UI.

Упрощение MUST быть явно скрыто за интерфейсом/адаптером, чтобы его можно было заменить без переписывания доменной логики.

## 87. Запрещённые компромиссы

Даже для демо запрещено:

- рассчитывать итоговый Match Score внутри LLM prompt;
- принимать автоматическое решение «нанять/отказать»;
- использовать пол, возраст, национальность, фотографию или другие protected attributes;
- возвращать фиктивный успешный статус после фактической ошибки;
- хранить пароль в открытом виде;
- обходить tenant authorization;
- давать employer доступ к приватному кандидату без разрешённого сценария;
- списывать usage дважды из-за retry;
- скрывать пользователю, что часть данных является demo fixture;
- включать незавершённые функции в основной demo path.

# Часть XVIII. Полная операционная модель продукта

## 88. Состояния аккаунта пользователя

Аккаунт имеет статус:

- `pending_verification`;
- `active`;
- `suspended`;
- `deletion_requested`;
- `deleted`.

Переходы:

1. регистрация создаёт `pending_verification` или сразу `active` в demo mode;
2. успешная верификация переводит в `active`;
3. admin/security action переводит в `suspended`;
4. запрос удаления переводит в `deletion_requested`;
5. завершение retention workflow переводит в `deleted`.

Suspended account не может создавать новые данные, но его данные не удаляются автоматически.

## 89. Полный сценарий регистрации кандидата

### 89.1 Happy path

1. Пользователь открывает `/register`.
2. Выбирает роль Candidate.
3. Вводит email, password, password confirmation.
4. Принимает Terms и Privacy.
5. Frontend валидирует обязательные поля.
6. Backend нормализует email.
7. Backend проверяет уникальность email.
8. Пароль хэшируется.
9. Создаётся user.
10. Создаётся пустой candidate profile.
11. Создаётся audit event `user_registered`.
12. Возвращаются access/refresh tokens либо verification requirement.
13. Пользователь перенаправляется в onboarding.

### 89.2 Ошибки

- email уже существует → `409 EMAIL_ALREADY_EXISTS`;
- слабый пароль → `422 PASSWORD_POLICY_FAILED`;
- terms не приняты → `422 CONSENT_REQUIRED`;
- rate limit → `429 RATE_LIMITED`;
- database error → generic `500`, без утечки внутренней информации.

## 90. Candidate onboarding

Onboarding состоит из пяти шагов:

1. базовая информация;
2. целевая роль;
3. загрузка резюме;
4. GitHub repository;
5. подтверждение анализа.

Пользователь может пропустить GitHub, но интерфейс показывает, что confidence будет ниже.

Базовая информация:

- имя;
- фамилия;
- headline;
- страна/город;
- preferred work format;
- target role;
- experience level;
- optional bio.

Protected attributes не запрашиваются для scoring.

После каждого шага данные сохраняются отдельно. Возврат на предыдущий шаг не должен терять введённые данные.

## 91. Resume operation flow

### 91.1 Upload

1. Candidate выбирает файл.
2. Frontend проверяет расширение и размер.
3. Backend повторно проверяет размер, extension и MIME.
4. Генерируется безопасное server-side имя.
5. Файл сохраняется.
6. Создаётся Resume record со статусом `uploaded`.
7. Предыдущий active resume переводится в `superseded`, если политика допускает только один active resume.
8. Создаётся parsing job.
9. API возвращает resume_id и job_id.
10. Frontend начинает polling.

### 91.2 Parsing

1. Job `pending` → `running`.
2. Из файла извлекается текст.
3. Пустой или слишком короткий текст считается ошибкой качества.
4. Plain text сохраняется только во внутреннем `Resume.extracted_text`; он не возвращается
   публичным API.
5. Одной транзакцией Job становится `completed`, а Resume переходит `uploaded` → `parsed`.
6. Structured extraction, contacts, education, projects, skills, Evidence, Skill Passport, AI
   analysis и matching выполняются отдельными последующими модулями и не являются частью этого
   worker.

### 91.3 Parsing failures

Статусы ошибок:

- `unsupported_format`;
- `file_too_large`;
- `corrupted_file`;
- `empty_text`;
- `extractor_timeout`;
- `internal_error`.

Пользователь видит действие: повторить, загрузить другой файл или продолжить без resume.

## 92. GitHub repository flow

1. Candidate вводит URL публичного repository.
2. Backend проверяет HTTPS URL и допустимый host.
3. URL нормализуется в owner/repository.
4. Создаётся repository source.
5. Запускается scan job.
6. Получаются metadata, languages, default branch, README, file tree и выбранные manifest files.
7. Секреты и содержимое `.env` не извлекаются.
8. Детектируются технологии по manifest/config files.
9. Формируются evidence units.
10. Сохраняется repository snapshot и checksum.
11. Skill Passport пересчитывается.

Hackathon MVP MUST NOT исполнять пользовательский код.

Ошибки:

- repository не найден;
- private repository;
- rate limit GitHub;
- malformed URL;
- слишком большой repository;
- network timeout.

В demo mode система MAY применить сохранённый snapshot, но UI должен маркировать это как demo data.

### 92.1 Семантика подключения GitHub repository

У кандидата может быть не более одного GitHub repository source.

Подключение выполняется после нормализации URL в canonical URL.

Если у кандидата уже существует GitHubRepository с тем же canonical URL, операция
идемпотентна: возвращается существующая запись, новая запись не создаётся, timestamps вручную не
изменяются, provider и scan не запускаются.

Если у кандидата уже существует GitHubRepository с другим canonical URL, возвращается внутренняя
domain/service conflict error. Существующая запись не заменяется и не удаляется, новая запись не
создаётся.

Автоматическая replacement semantics отсутствует. Disconnect и explicit replacement не входят в
Stage 7.3 и требуют отдельного определения/этапа.

Provider verification при подключении не выполняется. Metadata получается позднее на этапе scan.

### 92.2 Внутренние подэтапы scan pipeline

Полный scan сохраняет repository snapshot и checksum, а также создаёт EvidenceUnit согласно §92.

Stage 7.4A является внутренним read-only шагом полного pipeline: он получает и проверяет snapshot,
но не считается завершённым пользовательским scan. Его валидированный результат передаётся в
отдельный Stage 7.4B для persistence snapshot и checksum. EvidenceUnit generation выполняется
отдельным Stage 7.5.

### 92.3 GitHub repository snapshot persistence

Для каждого GitHubRepository хранится не более одного актуального snapshot; история snapshots на
текущем этапе не ведётся. Snapshot хранится в отдельной таблице GitHubRepositorySnapshot и
принадлежит ровно одному GitHubRepository. `repository_id` уникален, `candidate_id` не дублируется.

Persisted snapshot содержит только normalized provider data: canonical_url, owner, repository_name,
description, default_branch, is_public, is_archived, languages, tree_paths, readme_text,
manifest_paths и provider/demo indicator. Raw GitHub API payload не сохраняется. Payload хранится
в JSONB; отдельные поля таблицы: id, repository_id, checksum, payload, created_at, updated_at.

Перед checksum snapshot сериализуется в canonical JSON с фиксированным набором полей, сортировкой
ключей, UTF-8 без незначащих пробелов и ASCII-экранирования. Порядок коллекций сохраняется;
optional values сериализуются как null; дополнительные поля запрещены. Checksum — SHA-256 от UTF-8
bytes canonical JSON в lowercase hexadecimal длиной 64. Одинаковый checksum означает
семантически неизменившийся persisted snapshot.

Первый scan создаёт snapshot, payload и checksum. При повторном scan с тем же checksum возвращается
существующий snapshot без изменения payload/checksum, flush и ручного изменения timestamps. При
другом checksum payload и checksum заменяются; updated_at обновляется обычным ORM/DB механизмом,
created_at сохраняется. Bounds: languages до 20, tree_paths до 500, manifest_paths до 50, README до
10 000 символов; persistence повторно их валидирует.

Stage 7.4B не создаёт EvidenceUnit. Stage 7.5 использует актуальный persisted snapshot для
EvidenceUnit generation; прямого FK между snapshot и EvidenceUnit нет.

### 92.4 GitHub Evidence Generation

Для каждого подключённого `GitHubRepository` существует ровно один актуальный repository-level
`EvidenceUnit`. Отдельные EvidenceUnit для languages, README, manifest files, default branch,
tree paths или отдельных файлов не создаются.

Этот EvidenceUnit строится только из актуального persisted `GitHubRepositorySnapshot`. Его
`source_type` всегда равен `github_repository`, а `source_reference` — canonical GitHub URL из
snapshot без checksum, snapshot ID, query, branch, commit или timestamp. Дедупликационный ключ —
`(candidate_id, source_type, source_reference)`; для него существует не более одной актуальной
записи.

Поля проецируются детерминированно:

- `title`: `GitHub repository: {owner}/{repository_name}`;
- `description`: trimmed `snapshot.description`, если он непустой; иначе
  `Public GitHub repository {owner}/{repository_name}.`;
- `observed_at` и `freshness_at`: `GitHubRepositorySnapshot.updated_at`;
- `issued_at`: `NULL`;
- `verification_status`: `source_reachable`, поскольку публичный источник был непосредственно
  получен системой;
- `ownership_status`: `unverified`. В Stage 7 public repository connection без GitHub OAuth не
  подтверждает ownership и никогда не устанавливает `verified`;
- `strength_score`: `1.00` — базовая сила `Relevant public code repository` из §12.2. Отсутствие
  README/description/manifests, archived status и малый tree не изменяют score;
- `raw_payload_reference`: `github_repository_snapshot:{snapshot.id}` с каноническим строковым
  представлением ID. Payload повторно внутри EvidenceUnit не хранится.

`quality_flags` — JSON object ровно со следующими boolean-полями, без дополнительных ключей:

```json
{
  "archived": false,
  "missing_description": false,
  "missing_readme": false,
  "missing_languages": false,
  "empty_file_tree": false,
  "missing_manifests": false
}
```

`archived` равен `snapshot.is_archived == true`; `missing_description` и `missing_readme` равны
отсутствию либо пустому значению после trim соответствующего текста; `missing_languages`,
`empty_file_tree` и `missing_manifests` равны пустоте соответствующих коллекций. Эти flags не
изменяют strength score на Stage 7.

Generation service повторно проверяет identity repository и snapshot: canonical URL, owner и
repository_name. Он не вызывает provider, сеть или fetch, не создаёт snapshot, не делает commit
или rollback. После построения полей он ищет EvidenceUnit по дедупликационному ключу. При
отсутствии записи он создаёт её, делает flush и возвращает `created=True, changed=True`. Если все
управляемые Stage 7.5 поля совпадают, он возвращает существующую запись без mutation и flush с
`created=False, changed=False`. При любом отличии управляемого поля он обновляет эту же запись in
place, делает flush и возвращает `created=False, changed=True`.

Управляемые Stage 7.5 поля: `source_type`, `source_reference`, `title`, `description`,
`observed_at`, `issued_at`, `freshness_at`, `verification_status`, `ownership_status`,
`strength_score`, `quality_flags` и `raw_payload_reference`. Другие поля service не изменяет.

При неизменившемся snapshot Stage 7.4B не меняет `snapshot.updated_at`, поэтому EvidenceUnit не
изменяется, не flush-ится и его timestamps не обновляются. При изменившемся snapshot Stage 7.5
обновляет тот же EvidenceUnit in place; новый EvidenceUnit не создаётся. Stage 7.5 не удаляет,
не soft-delete-ит и не помечает evidence устаревшим; disconnect/removal repository определяется
отдельным этапом.

Service владеет только flush. Внешний transaction boundary владеет commit, rollback и retry.
UNIQUE constraint защищает от конкурентного создания одинакового EvidenceUnit; `IntegrityError`
не преобразуется в успешную идемпотентность и пробрасывается наружу без rollback внутри service.
Типизированные внутренние ошибки используются для отсутствующих CandidateProfile,
GitHubRepository или GitHubRepositorySnapshot, malformed stored repository URL, identity mismatch
и persisted snapshot payload, не соответствующего ожидаемой canonical schema.

## 93. Skill Passport rebuild

Rebuild запускается при:

- успешном resume parsing;
- успешном GitHub scan;
- изменении candidate profile;
- добавлении assessment;
- изменении skill ontology version;
- ручном reanalyze;
- истечении freshness policy.

Алгоритм:

1. создать immutable profile snapshot;
2. собрать активные evidence units;
3. нормализовать skill aliases;
4. сгруппировать evidence по skill;
5. вычислить evidence strength;
6. вычислить skill score;
7. вычислить skill confidence;
8. определить статус declared/supported/verified;
9. вычислить passport completeness;
10. сформировать gaps относительно target role;
11. сохранить новую passport version;
12. пометить старую версию current=false;
13. инвалидировать устаревшие match results;
14. опубликовать domain event `passport_rebuilt`.

## 94. Employer registration and workspace

Hackathon MVP:

1. пользователь выбирает Employer;
2. вводит email/password;
3. вводит company name;
4. создаются user, organization и membership с ролью owner;
5. открывается employer dashboard.

Commercial MVP дополнительно:

- email/domain verification;
- приглашение участников;
- роли owner/admin/recruiter/viewer;
- seat enforcement;
- legal entity and billing profile;
- trial activation;
- audit trail.

## 95. Vacancy lifecycle

Статусы вакансии:

- `draft`;
- `normalizing`;
- `ready_for_review`;
- `published`;
- `paused`;
- `closed`;
- `archived`.

### 95.1 Создание

Поля MVP:

- title;
- description;
- location;
- work format;
- employment type;
- seniority;
- required skills;
- optional skills;
- minimum skill levels;
- requirement importance;
- language requirements;
- experience expectations.

### 95.2 Нормализация

1. Recruiter сохраняет draft.
2. AI MAY предложить canonical skills и разделить must-have/nice-to-have.
3. Backend не публикует изменения автоматически.
4. Recruiter подтверждает требования.
5. Backend валидирует, что есть хотя бы один requirement.
6. Создаётся immutable vacancy version.
7. Vacancy готова к публикации.

### 95.3 Публикация

Перед публикацией проверяется:

- organization access;
- active vacancy limit;
- наличие title/description;
- подтверждение requirement set;
- отсутствие запрещённых discriminatory requirements;
- наличие current vacancy version.

После публикации запускается matching against visible candidates.

### 95.4 Изменение опубликованной вакансии

Изменение requirements создаёт новую vacancy version. Старые match results сохраняются для аудита, но current ranking пересчитывается.

## 96. Matching operation

Для каждой допустимой пары candidate snapshot + vacancy version:

1. проверить visibility/eligibility;
2. загрузить current passport;
3. сопоставить canonical skills;
4. вычислить coverage must-have;
5. вычислить coverage nice-to-have;
6. учесть evidence strength;
7. учесть confidence;
8. применить только разрешённые caps/penalties;
9. сформировать deterministic score;
10. сформировать factor breakdown;
11. LLM MAY сформулировать human-readable explanation только из breakdown;
12. сохранить MatchResult;
13. добавить в ranking.

Повторный запрос той же версии должен возвращать существующий результат, а не списывать новую usage unit.

## 97. Employer ranking

Таблица ranking MUST отображать:

- имя кандидата;
- target/headline;
- Match Score;
- Match Confidence;
- количество подтверждённых must-have skills;
- количество gaps;
- top evidence sources;
- application/invitation status;
- last passport update.

Сортировка по умолчанию:

1. Match Score descending;
2. Confidence descending;
3. passport freshness descending.

Recruiter может фильтровать по:

- minimum score;
- confidence;
- must-have coverage;
- location/work format;
- invitation status.

Фильтры не должны использовать protected attributes.

## 98. Candidate detail and employer actions

Recruiter видит:

- summary;
- Skill Passport;
- evidence per skill;
- Match breakdown;
- gaps;
- confidence limitations;
- resume preview/download при разрешении;
- repository links;
- activity history внутри своей organization.

Действия MVP:

- shortlist;
- remove from shortlist;
- invite;
- mark reviewed;
- add private note;
- return to ranking.

Commercial MVP:

- assign owner;
- team mentions;
- pipeline stages;
- rejection reason;
- bulk actions;
- export;
- webhook.

## 99. Invitation flow

1. Recruiter нажимает Invite.
2. Backend проверяет organization and vacancy access.
3. Проверяет, что vacancy published.
4. Проверяет idempotency — повторный click не создаёт дубликат.
5. Создаётся invitation/application event.
6. Candidate notification создаётся внутри продукта.
7. Candidate видит vacancy, score и message.
8. Candidate может принять, отклонить или оставить без ответа.
9. Recruiter видит актуальный статус.

MVP statuses:

- `sent`;
- `viewed`;
- `accepted`;
- `declined`;
- `expired`.

## 100. Candidate gap roadmap

Roadmap строится только из определённых gaps и должен содержать 3–5 действий.

Каждое действие содержит:

- gap skill;
- почему skill важен;
- ожидаемый evidence;
- конкретное действие;
- пример результата;
- estimated effort band;
- priority;
- completion state.

Пример: не «изучи Docker», а «добавь Dockerfile и docker-compose к выбранному проекту, запусти сервис и приложи README с командами запуска».

LLM MAY формулировать текст, но priority определяется детерминированно из vacancy weight и текущего gap.

# Часть XIX. Подписки, цены и права доступа

## 101. Принцип монетизации

Кандидатский core experience остаётся бесплатным. Основной плательщик — организация-работодатель. Компания платит за сокращение времени screening, объяснимый ranking, совместную работу и объём обработанных кандидатов.

Тарифы ниже являются стартовой коммерческой политикой версии 4.0. Изменение цены требует новой версии specification.

## 102. Entitlement matrix

| Функция | Trial | Starter | Growth | Agency | Scale | Enterprise |
|---|---:|---:|---:|---:|---:|---:|
| Цена в месяц | $0 / 14 дней | $199 | $749 | $1,499 | $2,499 | от $42,000/год |
| Активные вакансии | 1 | 3 | 15 | 30 | 50 | договор |
| Candidate Analysis Units/мес | 50 | 300 | 2,000 | 3,000 | 10,000 | договор |
| Seats | 2 | 3 | 10 | 10 | 30 | договор |
| Skill Passport | Да | Да | Да | Да | Да | Да |
| Match + Confidence | Да | Да | Да | Да | Да | Да |
| Explainability | Базовая | Полная | Полная | Полная | Полная | Полная |
| Shortlist | Да | Да | Да | Да | Да | Да |
| Team notes | Нет | Базовые | Да | Да | Да | Да |
| Advanced filters | Нет | Ограниченно | Да | Да | Да | Да |
| CSV export | Нет | 100 строк/мес | 5,000 строк/мес | 10,000 строк/мес | 50,000 строк/мес | договор |
| Vacancy templates | Нет | 3 | 25 | Без лимита | Без лимита | Без лимита |
| Analytics | Нет | Базовая | Расширенная | Agency | Advanced | Custom |
| Webhooks | Нет | Нет | Да | Да | Да | Да |
| API | Нет | Нет | Add-on/ограниченно | Add-on | Да | Да |
| Client workspaces | Нет | Нет | Нет | Да | Нет | Custom |
| SSO/SAML | Нет | Нет | Нет | Нет | Add-on readiness | Да |
| SLA | Нет | Нет | Нет | Нет | Business | Contract |
| Support | Community | Email | Priority | Priority | Dedicated contact | Dedicated team |

## 103. Trial

Trial начинается при создании первой employer organization.

Trial заканчивается при наступлении первого события:

- прошло 14 дней;
- использовано 50 Candidate Analysis Units;
- пользователь вручную активировал платный план.

После окончания:

- organization переходит в read-only;
- existing vacancies и results доступны;
- публикация новой вакансии и новый анализ блокируются;
- данные не удаляются;
- показывается upgrade screen.

Для design partner admin MAY продлить trial вручную с audit event.

## 104. Starter — $199/month

Предназначен для небольшой компании с нерегулярным наймом.

Пользователь получает:

- до 3 опубликованных вакансий одновременно;
- 300 уникальных candidate analyses в billing period;
- до 3 employer users;
- полный Skill Passport;
- Match Score, Confidence и factor explanation;
- shortlist;
- базовые private notes;
- 3 vacancy templates;
- до 100 строк CSV export в месяц;
- email support.

Не получает:

- webhooks;
- API;
- advanced analytics;
- SSO;
- client workspaces;
- bulk export.

Overage: $1.00 за Candidate Analysis Unit при включённом overage.

## 105. Growth — $749/month

Предназначен для команды, которая нанимает постоянно.

Включает Starter плюс:

- 15 active vacancies;
- 2,000 analyses;
- 10 seats;
- advanced filters;
- shared notes and ownership;
- funnel analytics;
- 25 vacancy templates;
- webhooks;
- ATS-friendly export;
- priority support;
- до 5,000 строк export.

Overage: $0.75/unit.

## 106. Agency — $1,499/month

Предназначен для рекрутингового агентства.

Включает:

- 30 active client vacancies;
- 3,000 analyses;
- 10 seats;
- отдельные client workspaces;
- branded candidate report;
- unlimited vacancy templates;
- agency-level analytics;
- reusable candidate pools;
- до 10,000 строк export;
- webhooks.

Overage: $0.65/unit.

Agency workspace данные одного клиента MUST быть изолированы от другого клиента.

## 107. Scale — $2,499/month

Предназначен для high-volume hiring.

Включает:

- 50 active vacancies;
- 10,000 analyses;
- 30 seats;
- API access;
- advanced analytics;
- audit export;
- custom retention presets;
- dedicated success contact;
- business support target;
- до 50,000 строк export.

Overage: $0.50/unit.

## 108. Enterprise — от $42,000/year

Цена формируется из объёма, интеграций, security и SLA.

Возможные включения:

- custom analyses;
- custom seats;
- SSO/SAML;
- SCIM;
- DPA/SCC;
- security review;
- private networking roadmap;
- regional data residency roadmap;
- custom retention;
- named support;
- custom API limits;
- ATS integration;
- bias audit exports;
- dedicated model/provider configuration.

Enterprise функции не входят в пятидневный MVP.

## 109. Candidate monetization

Бесплатно навсегда:

- профиль;
- resume upload;
- один активный Skill Passport;
- базовые evidence;
- match results для доступных вакансий;
- gaps;
- базовый roadmap;
- invitations;
- privacy controls.

Опционально после Commercial MVP:

- Deep Profile Review — $29 one-off;
- Advanced Career Report — $19;
- Interview Readiness Pack — $29;
- Assessment Pack — $15–$39;
- Human Expert Review — marketplace price.

Покупка candidate premium MUST NOT повышать score, ranking или confidence сама по себе.

## 110. Billing events

Billable event создаётся только после сохранения валидного результата.

Billable:

- новый general passport analysis по новому snapshot;
- новый vacancy match по существенно новой vacancy version;
- deep repository analysis;
- premium assessment report.

Не billable:

- page refresh;
- retry после failed job;
- повторное чтение результата;
- изменение имени кандидата без влияния на evidence;
- системный recalculation из-за bug fix;
- demo fixture;
- admin test.

## 111. Upgrade, downgrade, cancellation

Upgrade:

- применяется немедленно;
- новые limits доступны сразу;
- proration делегируется payment provider;
- audit event обязателен.

Downgrade:

- применяется со следующего period;
- система заранее показывает конфликты limits;
- данные не удаляются;
- лишние vacancies становятся paused только после начала нового периода;
- лишние seats требуют выбора admin.

Cancellation:

- действует в конце периода;
- до конца периода функции сохраняются;
- затем organization read-only минимум 30 дней;
- экспорт данных доступен;
- восстановление возможно в retention window.

Refunds и taxes обрабатываются payment provider и политикой компании; автоматическая логика возвратов не входит в MVP.

# Часть XX. Полная карта интерфейсов и состояний

## 112. Public site

Обязательные страницы:

- `/` — landing;
- `/pricing` — тарифы;
- `/login`;
- `/register`;
- `/privacy`;
- `/terms`.

Landing MUST объяснять:

1. проблема: резюме не доказывает навыки;
2. решение: evidence-based Skill Passport;
3. employer value: быстрый объяснимый shortlist;
4. candidate value: показать реальные способности;
5. CTA Candidate и Employer;
6. как работает продукт в 3 шага;
7. trust/fairness statement;
8. pricing preview.

## 113. Candidate screens

### 113.1 Dashboard

Карточки:

- profile completeness;
- analysis status;
- Skill Passport summary;
- target role readiness;
- top strengths;
- top gaps;
- current invitations;
- recommended next action.

Состояния:

- no profile;
- no resume;
- parsing;
- parsing failed;
- no GitHub;
- analysis running;
- passport ready;
- passport stale;
- no invitations;
- invitations present.

### 113.2 Resume page

Действия:

- upload;
- replace;
- view status;
- retry;
- delete subject to retention rules.

### 113.3 GitHub page

Действия:

- add URL;
- scan;
- rescan;
- disconnect;
- view detected evidence.

### 113.4 Skill Passport page

Секции:

- summary;
- completeness/confidence;
- skill groups;
- evidence drawer;
- unverified claims;
- gaps;
- version/freshness;
- reanalyze button.

### 113.5 Invitations

Список и detail. Candidate может accept/decline.

## 114. Employer screens

### 114.1 Dashboard

- active vacancies;
- candidate analyses usage;
- recent matches;
- invitations awaiting response;
- trial/plan banner;
- CTA Create vacancy.

### 114.2 Vacancy wizard

Шаги:

1. basics;
2. requirements;
3. AI normalization review;
4. publish confirmation.

Draft autosave SHOULD быть реализован в Commercial MVP; для Hackathon достаточно Save and continue.

### 114.3 Ranking

Обязательны loading, empty, error и populated states.

### 114.4 Candidate detail

Обязательны explainability и limitations; score без breakdown показывать запрещено.

### 114.5 Billing

В Hackathon MVP — read-only pricing/plan mock с реальной entitlement configuration. Commercial MVP — subscription management.

## 115. Общие UI правила

Для каждой async операции должны существовать:

- idle;
- loading;
- success;
- validation error;
- recoverable error;
- non-recoverable error.

Кнопка во время запроса disabled. Повторный click не создаёт duplicate operation. Ошибка содержит понятное действие.

# Часть XXI. Каркас для будущего расширения

## 116. Архитектурные интерфейсы, обязательные уже в MVP

Даже если реализация упрощена, должны существовать абстракции:

- `FileStorage` — local сейчас, S3 позже;
- `AIProvider` — demo/LLM adapters;
- `GitHubProvider` — live/fixture adapters;
- `PaymentProvider` — noop сейчас, Stripe/другой позже;
- `NotificationProvider` — in-app сейчас, email/SMS позже;
- `JobRunner` — BackgroundTasks сейчас, queue позже;
- `AuditSink` — database сейчас, external SIEM позже;
- `AssessmentProvider` — internal сейчас, integrations позже.

Доменные сервисы не должны зависеть напрямую от конкретного внешнего SDK.

## 117. Feature flags

Предусмотреть конфигурационные flags:

- `DEMO_MODE`;
- `AI_PROVIDER`;
- `GITHUB_LIVE_ENABLED`;
- `BILLING_ENABLED`;
- `EMAIL_ENABLED`;
- `ASSESSMENTS_ENABLED`;
- `PUBLIC_CANDIDATE_DISCOVERY_ENABLED`;
- `API_ACCESS_ENABLED`.

Feature flag не заменяет authorization.

## 118. Версионирование ключевых моделей

Версионируются:

- skill ontology;
- scoring formula;
- passport;
- vacancy requirements;
- match result;
- AI extraction schema;
- terms/privacy consent;
- plan definition.

Каждый result хранит версии зависимостей, чтобы его можно было объяснить позже.

## 119. Future integration points

Каркас должен позволять добавить:

- ATS webhooks/API;
- university cohort import;
- certificate issuers;
- GitLab/Bitbucket;
- coding assessment providers;
- SSO/SCIM;
- object storage;
- payment processor;
- analytics warehouse;
- transactional email;
- audit export.

Ни одна из этих интеграций не должна блокировать пятидневный MVP.

# Часть XXII. Пятидневный план исполнения

## 120. День 1 — freeze продукта и backend foundation completion

Цель: к концу дня спецификация заморожена, data model и job flow готовы.

Обязательные результаты:

- версия 4.0 утверждена;
- backlog разделён на MUST/SHOULD/FUTURE;
- реализован/проверен resume parsing job;
- создан jobs polling API;
- подготовлены seed/demo accounts;
- определены UI routes;
- зафиксирована scoring formula v1;
- все текущие tests проходят, кроме четырёх намеренно исключённых black files.

Stop condition: после freeze новые идеи не входят в MVP без удаления равного или большего scope.

## 121. День 2 — GitHub, evidence, passport

Обязательные результаты:

- repository model/API;
- safe scan или deterministic fixture adapter;
- evidence units;
- skill normalization;
- Skill Passport v1;
- passport API;
- unit/integration tests;
- candidate frontend: onboarding, resume status, GitHub, passport basic view.

## 122. День 3 — vacancy and matching

Обязательные результаты:

- employer account/workspace simplified;
- vacancy CRUD and publish;
- requirements confirmation;
- deterministic Match Score;
- Confidence Score;
- factor breakdown;
- gaps;
- ranking API;
- employer frontend: vacancy wizard and ranking.

## 123. День 4 — invitation, integration, UX hardening

Обязательные результаты:

- candidate detail;
- shortlist/invite;
- candidate invitation view;
- roadmap;
- complete end-to-end frontend;
- loading/empty/error states;
- integration tests;
- demo seed/reset command;
- bug triage.

Запрещено начинать крупные новые функции после середины дня 4.

## 124. День 5 — stabilization and pitch

Только:

- P0/P1 bug fixes;
- responsive/polish;
- performance of demo path;
- clean setup instructions;
- production-like demo deployment;
- demo script;
- screenshots/video fallback;
- pitch deck and rehearsal;
- backup demo data.

Новые backend modules и product features в день 5 запрещены.

## 125. Приоритеты дефектов

- **P0:** приложение не запускается, data loss, auth bypass, основной demo flow сломан.
- **P1:** одна ключевая операция не работает, score неверен, ranking/invitation недоступны.
- **P2:** частичный UX defect с workaround.
- **P3:** косметика.

До demo должны быть закрыты все P0 и P1. P2 исправляются по времени. P3 не блокируют release.

# Часть XXIII. Демонстрационный сценарий

## 126. Golden demo path

1. Открыть landing и за 20 секунд объяснить ценность.
2. Войти как Candidate.
3. Показать загруженное resume и завершённый parsing.
4. Подключить или показать GitHub repository.
5. Открыть Skill Passport и evidence.
6. Показать gap для выбранной роли.
7. Переключиться на Employer.
8. Создать/открыть Junior Backend vacancy.
9. Показать ranking нескольких кандидатов.
10. Открыть top candidate.
11. Показать, почему score высокий и где ограничения confidence.
12. Отправить invitation.
13. Вернуться к Candidate и принять invitation.
14. Завершить business model/pricing screen.

Максимальная длительность — 4 минуты.

## 127. Demo fallback

При недоступности GitHub/LLM:

- использовать заранее сохранённые provider fixtures;
- сохранять тот же доменный flow и jobs;
- маркировать demo mode;
- не менять score вручную перед показом.

Должен существовать reset command, который возвращает demo database в известное состояние.

# Часть XXIV. Матрица реализации требований

## 128. Обозначения

- `IMPLEMENTED` — уже работает;
- `MVP-MUST` — обязательно за пять дней;
- `MVP-SHOULD` — делать после MUST при наличии времени;
- `COMMERCIAL` — после хакатона;
- `FUTURE` — стратегическое расширение.

## 129. Requirement matrix

| Область | Функция | Приоритет |
|---|---|---|
| Auth | JWT register/login/refresh | IMPLEMENTED |
| Candidate | Profile CRUD | IMPLEMENTED |
| Resume | Upload | IMPLEMENTED |
| Resume | Text parsing | IMPLEMENTED |
| Jobs | Async-style parsing lifecycle + polling | MVP-MUST |
| GitHub | One repository scan | MVP-MUST |
| Evidence | Evidence units | MVP-MUST |
| Passport | Skill Passport v1 | MVP-MUST |
| Vacancy | Structured vacancy CRUD/publish | MVP-MUST |
| Matching | Deterministic score/confidence | MVP-MUST |
| Explainability | Breakdown and gaps | MVP-MUST |
| Employer | Ranking and candidate detail | MVP-MUST |
| Actions | Shortlist/invite | MVP-MUST |
| Candidate | Invitations | MVP-MUST |
| Roadmap | 3–5 concrete steps | MVP-MUST |
| UI | Complete responsive demo path | MVP-MUST |
| Billing | Pricing page and plan definitions | MVP-SHOULD |
| Billing | Real payments | COMMERCIAL |
| Teams | Membership/RBAC full | COMMERCIAL |
| Storage | S3 | COMMERCIAL |
| Email | Transactional email | COMMERCIAL |
| ATS | Webhook/export | COMMERCIAL |
| Enterprise | SSO/SCIM/SLA | FUTURE |
| Agency | Client workspaces | FUTURE |
| API | Public API | FUTURE |

# Часть XXV. Финальное правило изменения scope

## 130. Change control

После утверждения версии 4.0 любое изменение проходит процедуру:

1. описать проблему;
2. указать затрагиваемый сценарий;
3. определить уровень MVP/Commercial/Future;
4. оценить влияние на срок;
5. при добавлении MVP-функции удалить или упростить другой scope;
6. обновить specification;
7. провести review;
8. только затем реализовывать.

Устное решение, сообщение в чате или идея в коде не считается требованием, пока она не отражена в текущей версии документа.

## 131. Финальный продуктовый контракт

За пять дней BeyondResume должен доказать одну вещь:

> Из разрозненных доказательств junior-кандидата можно автоматически построить объяснимый Skill Passport и помочь работодателю быстрее выбрать кандидатов для человеческого рассмотрения.

Коммерческие функции должны быть предусмотрены архитектурно, но не имеют права ухудшать надёжность этого core promise.

# Приложение A. Главные бизнес-инварианты

1. Кандидат не платит за право быть объективно рассмотренным.
2. Оплата кандидата не повышает ranking.
3. Работодатель платит за workflow, signal quality и volume.
4. Один score никогда не показывается без confidence и explanation.
5. Отсутствие evidence не равно отсутствию способности.
6. AI не принимает adverse employment decisions.
7. Все billable usage events идемпотентны.
8. История scoring версионируется.
9. Изменение тарифа не переписывает прошлые usage события.
10. Закрытие подписки не удаляет candidate data без отдельного legal/privacy flow.
11. Employer видит кандидата только в разрешённом контексте.
12. Любой penalty объясним и оспорим.

# Приложение B. Рекомендуемый первый go-to-market

## B.1 Первый сегмент

- software studios;
- outsourcing companies;
- startups;
- recruiting agencies;
- команды, регулярно нанимающие junior backend developers.

## B.2 Design partner offer

- 4–6 week pilot;
- одна реальная junior vacancy;
- до 100–300 кандидатов;
- founder-led onboarding;
- baseline measurement до запуска;
- weekly feedback;
- discounted first annual contract.

## B.3 Что измеряется в pilot

- число заявок;
- ручное screening time до/после;
- shortlist size;
- interview conversion;
- recruiter agreement with explanation;
- false positive/negative examples;
- willingness to pay;
- renewal intent.

## B.4 Продажный тезис

Не продавать «AI». Продавать:

- быстрее разобрать поток;
- увидеть подтверждения;
- стандартизировать junior screening;
- объяснить shortlist hiring manager;
- запросить точное дополнительное evidence вместо общего теста.

# Приложение C. Финансовые сценарии

Ниже — ориентировочная управленческая модель, требующая пересчёта после первых продаж.

| Год | Conservative revenue | Realistic revenue | Aggressive revenue |
|---|---:|---:|---:|
| Y1 | $62k | $113k | $207k |
| Y2 | $320k | $690k | $1.38m |
| Y3 | $980k | $2.23m | $4.80m |

Ориентировочный OPEX funded team:

| Год | OPEX | CAPEX |
|---|---:|---:|
| Y1 | $550k | $30k |
| Y2 | $850k | $20k |
| Y3 | $1.20m | $25k |

Эти значения не должны использоваться как обещание инвесторам. Они служат для sensitivity planning.

Ключевые факторы сильнее всего влияющие на прибыльность:

1. pilot-to-paid conversion;
2. churn;
3. blended CAC;
4. annual contract share;
5. analysis volume per customer;
6. overage adoption;
7. LLM cost per unit;
8. support load.

# Приложение D. Источники и валидация гипотез

При подготовке бизнес-части использовались публичные рыночные ориентиры по:

- HR technology и ATS markets;
- pricing Workable, Indeed, Greenhouse, Lever и LinkedIn Recruiter;
- SaaS gross margin и CAC payback benchmarks;
- recruitment cost and time-to-fill benchmarks;
- cloud storage/compute pricing;
- regulatory guidance по automated recruitment и algorithmic fairness.

Рыночные цифры быстро меняются. Перед investor deck, pricing launch или финансовым решением они должны быть перепроверены на текущую дату по первичным и официальным источникам.

---

**Конец документа.**
