# KAPDA Digital Programme & Learner Tracking System

A modular Django foundation designed around KAPDA's supplied requirements for EPICK II/future EPICK phases, BSLFSR, learner longitudinal tracking, school governance, MHM/WASH, project indicators and reporting.

## Included
- `core`: shared locations, audit events, academic years/terms, schools, age groups and common utilities.
- `accounts`: custom user/profile, roles and authentication by username, email, phone or RegNo.
- `projects`: projects, consolidated indicators/activities and submitted activity data.
- `learners`: persistent learner IDs, project participation, school enrolments, attendance, assessments, UNEB results, support distributions, class retention and status history.
- `monitoring`: activity plans/implementation, field visits, follow-up actions and MHM/WASH records.
- `school_governance`: SMC/PTA members, meetings, training, improvement plans and resolutions.
- `bslfsr`: beneficiaries, agriculture/extension and peacebuilding.
- `vsla_app.vsla`: the attached KAPDA-configured VSLA management module for groups, members, meetings, savings, loans and social funds.
- `reports`: dashboard, CSV learner export and filterable summary foundation.
- Staff access: `User` is the single unified staff account/profile model; job title, department and photo are stored directly on the NGO staff account. Learners, beneficiaries, farmers and VSLA participants are data subjects only and do not receive application accounts.
- In-app data workspace: staff can create, edit, search and delete programme records under `/data/` without using Django admin. Reports and exports are available under `/exports/` in CSV, Excel and PDF formats for learner and beneficiary registers.
- Learner and BSLFSR beneficiary records capture participant category (girl, boy, woman, man or other) and population/displacement status (host community, refugee, internally displaced, returnee, asylum seeker or other).
- Registration generates persistent IDs: `KAPDA-LEARNER-000001`, `KAPDA-BEN-000001`, `KAPDA-HH-000001`, `KAPDA-SCHOOL-0001` and `KAPDA-PC-0001`.

## Run locally
1. Python 3.10+ recommended.
2. `python -m venv .venv` and activate it.
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set a secure `DJANGO_SECRET_KEY`.
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py runserver`

The settings loader reads `.env` during development and environment variables in deployment. Never commit `.env`; use `.env.example` as the starting point. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` and `DATABASE_URL` as appropriate.

## Deployment

The project is configured for a WSGI deployment with Gunicorn and WhiteNoise. The included `Procfile` starts the application and `build.sh` runs migrations and collects static files. For production, set `DJANGO_DEBUG=False`, provide a strong `DJANGO_SECRET_KEY`, configure `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, and use PostgreSQL through `DATABASE_URL`. Uploaded media should be stored on durable object storage or a persistent volume; the local `media/` directory is ignored by Git.

Run `python manage.py check --deploy` against the production environment before release.

## First setup
Create projects, schools, academic years, terms and staff accounts in Django admin. Create a learner from the Learners page and assign the project/school/class. Class retention is restricted to staff with teacher, M&E, programme-manager or admin roles and requires an academic year and destination class.

## Important implementation notes
- Learner identity (`KAPDA-LEARNER-000001`) is persistent and independent of project, school or academic year.
- Class history is stored as separate enrolment records; retention does not overwrite previous years.
- Retention preview excludes terminal/withdrawn statuses and preserves S6/P7 completion as completion/transition workflows.
- S4 UNEB records are stored separately from routine term assessments.
- Sensitive child information should be minimized and access limited by role. Before production, add deployment-specific object-level school/project scope, consent/child-protection procedures, HTTPS, secure backups, logging/monitoring, and tests aligned to KAPDA policy and Uganda's applicable data-protection requirements.
- This is an implementation starter and requires programme validation, user acceptance testing, and migration planning before use with real child data.
