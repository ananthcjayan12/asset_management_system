# Asset Management System

A Dockerised Django 5.2 LTS modular-monolith application for asset identification, procurement, stock/installation, location responsibility, transfers, returns, temporary and permanent gate passes, disposal/auction, write-off/passout, staged Excel import, QR pages, audit history and reports.

## What is included

- Django Templates with local HTMX-compatible partial updates and offline UI assets.
- MySQL 8.4 in Docker Compose; SQLite fallback for local development/tests.
- Normalised asset, procurement, installation, movement, gate-pass, disposal, import and audit models.
- Atomic service functions for transfer, return and gate security actions.
- Role bootstrap for administrators, Stores, Divisions, Approvers, Security, Auditors and report viewers.
- Excel validation/preview/confirmation workflow and a ready-to-use template.
- QR label image and authenticated live asset webpage.
- Docker/IIS deployment examples, backup/restore scripts, tests and committed migrations.
- User and administrator manual in DOCX and PDF.

## Docker quick start

1. Extract the project to a controlled folder.
2. Copy `.env.example` to `.env`.
3. Replace every example password and `DJANGO_SECRET_KEY`.
4. For production, set `LOAD_DEMO_DATA=False`.
5. Run:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

6. On the server, open `http://127.0.0.1:8000/accounts/login/`.
7. Sign in using the administrator username/password from `.env`, then change the password immediately.

The default port binding is localhost-only for safe use behind IIS. When Docker runs in a separate private VM, set `APP_BIND_ADDRESS` to that VM's private interface and firewall it so only IIS can connect.

## Documentation

- `docs/Asset_Management_User_and_Admin_Manual.pdf`
- `docs/Asset_Management_User_and_Admin_Manual.docx`
- `docs/Administrator_Deployment_Guide.md`
- `docs/Validation_Report.md`
- `sample_data/Asset_Import_Template.xlsx`

## Development without Docker

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_system
python manage.py runserver
```

When MySQL environment variables are absent, development and automated tests use SQLite.

## Automated checks

```bash
python manage.py check
python manage.py test
python manage.py check --deploy
```

## Backup and restore

```bash
./deployment/backup.sh
./deployment/restore-example.sh backups/db-YYYYMMDD-HHMMSS.sql.gz
./deployment/restore-media-example.sh backups/media-YYYYMMDD-HHMMSS.tar.gz
```

Always test restoration in a non-production environment and keep encrypted off-server copies.

## Production security

- Keep `DJANGO_DEBUG=False`.
- Replace all example passwords and secrets.
- Configure HTTPS in IIS and set `DJANGO_SECURE_COOKIES=True`.
- Keep `QR_PAGE_PUBLIC=False` unless public visibility is formally approved.
- Restrict the application port to IIS or the private reverse-proxy interface.
- Review group permissions and disable/remove demo records.
- Complete user-acceptance, security, import-reconciliation and restore testing before go-live.
