# Asset Management System

A Dockerised Django 5.2 LTS modular-monolith application for asset identification, procurement, stock/installation, location responsibility, transfers, returns, temporary and permanent gate passes, disposal/auction, write-off/passout, staged Excel import, QR pages, audit history and reports.

## What is included

- Django Templates with local HTMX-compatible partial updates and offline UI assets.
- SQLite storage in a single Docker container, with one persistent data volume for the database and uploaded media.
- Normalised asset, procurement, installation, movement, gate-pass, disposal, import and audit models.
- Atomic service functions for transfer, return and gate security actions.
- Role bootstrap for administrators, Stores, Divisions, Approvers, Security, Auditors and report viewers.
- Excel validation/preview/confirmation workflow and a ready-to-use template.
- QR label image and authenticated live asset webpage.
- Docker/Coolify deployment instructions, backup/restore scripts, tests and committed migrations.
- User and administrator manual in DOCX and PDF.

## Docker quick start

1. Extract the project to a controlled folder.
2. Copy `.env.example` to `.env`.
3. Replace the example administrator password and `DJANGO_SECRET_KEY`.
4. Keep `LOAD_DEMO_DATA=True` for the demo records, or set it to `False` for an empty system.
5. Run:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

6. On the server, open `http://127.0.0.1:8000/accounts/login/`.
7. Sign in using the administrator username/password from `.env`, then change the password immediately.

The default port binding is localhost-only. SQLite and uploaded media are stored together in the persistent `app_data` volume.

## Coolify deployment

This follows the same deployment model as `realfibre-app-server`: Coolify builds the repository Dockerfile and runs one application container. Coolify automatically creates the proxy and Traefik labels.

Create a new Coolify application with these values:

- Source repository: `ananthcjayan12/asset_management_system`
- Branch: `main`
- Build pack: `Dockerfile`
- Dockerfile location: `/Dockerfile`
- Base directory: `/`
- Exposed port: `8000`
- Health check path: `/accounts/login/`
- Persistent storage destination: `/app/data`

Add the variables from `.env.example` in Coolify. Set the real domain in `DJANGO_ALLOWED_HOSTS`, put its complete HTTPS URL in `DJANGO_CSRF_TRUSTED_ORIGINS`, and set `DJANGO_SECURE_COOKIES=True`. Do not configure a public port mapping or custom Traefik labels; the Coolify domain setting handles HTTPS routing.

`DJANGO_SERVE_MEDIA=True` lets this demo container serve uploaded files directly. It avoids adding object storage or a separate web server.

After the first successful deployment, sign in with the configured administrator account. Automatic deployment can then be enabled for pushes to `main`.

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

Development and automated tests use SQLite. When running outside Docker, omit `SQLITE_DATABASE_PATH` and `DJANGO_MEDIA_ROOT` to use `db.sqlite3` and `media/` in the repository directory.

## Automated checks

```bash
python manage.py check
python manage.py test
python manage.py check --deploy
```

## Backup and restore

```bash
./deployment/backup.sh
./deployment/restore-example.sh backups/db-YYYYMMDD-HHMMSS.sqlite3
./deployment/restore-media-example.sh backups/media-YYYYMMDD-HHMMSS.tar.gz
```

Always test restoration in a non-production environment and keep encrypted off-server copies.

## Production security

- Keep `DJANGO_DEBUG=False`.
- Replace all example passwords and secrets.
- Configure the public HTTPS domain in Coolify and set `DJANGO_SECURE_COOKIES=True`.
- Keep `QR_PAGE_PUBLIC=False` unless public visibility is formally approved.
- Do not publish a host port in Coolify; route port 8000 through Coolify's proxy.
- Review group permissions and disable/remove demo records.
- Complete user-acceptance, security, import-reconciliation and restore testing before go-live.

## Guided Playwright feature tour

A visible end-to-end demonstration and debugging suite is included under `e2e/`. It creates isolated `PWDEMO-*` records and temporary administrator/report-viewer accounts, demonstrates the main workflows one by one, records screenshots/video/trace/server logs, downloads the CSV report, and removes successful-run data automatically.

Install the development dependencies once:

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
```

Run the visible tour:

```bash
python e2e/run_demo.py
```

Run the fast headless form used by CI:

```bash
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0
```

The runner uses a dedicated SQLite database under `e2e/artifacts/<timestamp>/` by default, so it does not modify the normal `db.sqlite3` data. Failure state is retained for debugging; successful data is cleaned automatically. See `e2e/README.md` for safety flags and trace viewing instructions.
