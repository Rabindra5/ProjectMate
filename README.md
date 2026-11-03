# ProjectMate

ProjectMate is a Django 5.2 web app for COMP-8347 Group 15 at the University of Windsor. It helps students discover project ideas, find teammates by skill, submit join requests, share resources, and review their activity history.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo --reset
.venv/bin/python manage.py runserver
```

Windows PowerShell uses `.venv\Scripts\python.exe` and `Copy-Item .env.example .env`.

Demo accounts: `admin`, `demo`, `owner_demo`, and `sam_student`. Password: `ProjectMate#2026`.

The default email backend prints password-reset messages to the console. Set `EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend` and `EMAIL_FILE_PATH=sent_emails` for file-based demos.

## Features

- Registration, email-or-username login, POST-only logout, profiles, links, password change, and reset.
- Project CRUD with categories, skills, status, images, deadlines, and owner permissions.
- Search filters, people finder, recommendations, skill management, and match percentages.
- Join requests, owner inbox decisions, memberships, leave/remove actions, and capacity synchronization.
- Session/cookie history, recent projects, activity dashboard, and public/team-only resources.
- Responsive Bootstrap 5.3 design system, light/dark theme cookie, accessibility landmarks, and custom errors.
- JSON fixtures, idempotent demo seeding, admin interfaces, and submission bundles.

## Testing

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
.venv/bin/python scripts/check_ownership.py
```

Run `.venv/bin/python scripts/e2e_smoke.py` while the development server is running for public route smoke coverage.

Use the prioritized [rubric testing checklist](docs/RUBRIC_TEST_CHECKLIST.md) before the presentation and submission. It maps each requirement to a test method and evidence to collect.

## PyCharm

Open this folder, select `.venv` as the Python interpreter, enable Django support, set `manage.py` as the Django project file, and create a run configuration for `runserver`.

## Submission and deployment

Run `.venv/bin/python scripts/build_submission.py` to regenerate `submission/`. Review [OWNERSHIP.md](OWNERSHIP.md), [docs/VIVA_GUIDE.md](docs/VIVA_GUIDE.md), and [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Use [docs/DEPLOY_PYTHONANYWHERE.md](docs/DEPLOY_PYTHONANYWHERE.md) for deployment preparation.
