# Administrator Deployment Guide

## Recommended topology

Windows Server 2022 hosts IIS. Docker Desktop/Engine or an Ubuntu Hyper-V virtual machine runs the `web` and `db` containers. IIS terminates HTTPS and reverse-proxies to `127.0.0.1:8000`.

## First deployment

1. Extract the project to a controlled folder such as `C:\AssetSystem` or `/opt/asset-system`.
2. Copy `.env.example` to `.env`.
3. Set a long random `DJANGO_SECRET_KEY`, MySQL passwords, allowed host name and trusted HTTPS origin.
4. Set `LOAD_DEMO_DATA=False` for production.
5. Run `docker compose up -d --build`.
6. Check `docker compose ps` and `docker compose logs -f web`.
7. Browse to `http://server:8000/accounts/login/` for an initial test.
8. Install IIS URL Rewrite and Application Request Routing, enable proxying, and adapt `deployment/iis-web.config.example`.
9. Bind the organisation's TLS certificate in IIS and redirect HTTP to HTTPS.
10. Set `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-hostname` and `DJANGO_SECURE_COOKIES=True`, then restart with `docker compose up -d`.

## Initial administration

Open `/admin/` and configure Divisions, Sections, Sub-sections, Locations, Employees, Suppliers, Users and Groups. Stock-return destinations must have `is_stock_location` selected.

## Roles

The bootstrap command creates System Administrator, Asset Administrator, Stores Officer, Division Officer, Approving Officer, Security Officer, Auditor and Report Viewer groups. Assign each user only the minimum necessary group.

## Backup

Back up both MySQL and the media volume. The provided `deployment/backup.sh` is an example for Linux shells. On Windows, run the equivalent commands from PowerShell or schedule them in Task Scheduler. Keep encrypted off-server copies and periodically test restoration.

## Upgrade

1. Take verified backups.
2. Review release notes and dependency changes.
3. Build a staging copy: `docker compose build --pull`.
4. Run tests and a representative workflow.
5. Deploy with `docker compose up -d --build`.
6. Review logs and run `docker compose exec web python manage.py check --deploy`.

## Troubleshooting

- Database connection errors: check `docker compose ps db`, passwords, and the `MYSQL_HOST=db` setting.
- CSRF errors behind IIS: verify the public HTTPS origin in `DJANGO_CSRF_TRUSTED_ORIGINS` and forwarded protocol header.
- Missing static styling: run `docker compose exec web python manage.py collectstatic --noinput` and restart.
- Permission denied: confirm the user's group and the corresponding Django permissions in `/admin/`.
- Import errors: open the batch page, inspect row-level validation messages, correct the workbook, and upload a new batch.

## Port binding

The supplied Compose file binds port 8000 to `127.0.0.1` by default. If Docker runs in an Ubuntu Hyper-V VM, set `APP_BIND_ADDRESS` to the VM's private interface and permit access only from the IIS server using the Windows/Linux firewall.

## Restore examples

- Database: `./deployment/restore-example.sh backups/db-YYYYMMDD-HHMMSS.sql.gz`
- Media: `./deployment/restore-media-example.sh backups/media-YYYYMMDD-HHMMSS.tar.gz`

Both examples require an explicit `RESTORE` confirmation. Restore into staging first, validate record counts and uploaded files, and only then plan a controlled production restore.
