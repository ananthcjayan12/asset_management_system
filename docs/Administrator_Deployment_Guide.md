# Administrator Deployment Guide

## Recommended topology

Deploy the repository as one Dockerfile application in Coolify. The container runs Django with Gunicorn on port 8000. Coolify terminates HTTPS and automatically adds the Traefik routing configuration.

SQLite and uploaded media share one persistent directory:

- Database: `/app/data/db.sqlite3`
- Uploaded media: `/app/data/media`
- Coolify persistent storage destination: `/app/data`

## First deployment

1. Push the repository to `ananthcjayan12/asset_management_system`.
2. In Coolify, create a project and a production environment.
3. Add a public GitHub application from the repository and select the `main` branch.
4. Select the Dockerfile build pack, base directory `/`, Dockerfile location `/Dockerfile`, and exposed port `8000`.
5. Add one persistent volume with destination `/app/data`.
6. Add the environment variables from `.env.example`.
7. Set `DJANGO_ALLOWED_HOSTS` to the public hostname.
8. Set `DJANGO_CSRF_TRUSTED_ORIGINS` to the complete public HTTPS origin.
9. Set `DJANGO_SECURE_COOKIES=True`, use a long random `DJANGO_SECRET_KEY`, and replace the sample administrator password.
10. Configure the domain in Coolify and deploy.

No custom Traefik labels, reverse-proxy files, database service, or host port mapping are required. Coolify routes the domain to container port 8000.

The container startup script applies migrations, collects static files, creates the standard groups, and optionally loads demo records. Use `LOAD_DEMO_DATA=True` for the demonstration system.

## Coolify settings

- Build pack: Dockerfile
- Dockerfile: `/Dockerfile`
- Base directory: `/`
- Port: `8000`
- Health check: `/accounts/login/`
- Force HTTPS: enabled
- Automatic deployment: enabled after the first verified deployment
- Preview deployments: disabled unless specifically needed

## Initial administration

Open `/admin/` and sign in with `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`. The password is only reset when the user is first created or `RESET_ADMIN_PASSWORD=True`.

Set `RESET_ADMIN_PASSWORD=False` after any intentional password reset. Configure Divisions, Sections, Sub-sections, Locations, Employees, Suppliers, Users, and Groups as needed.

## Backup

For local Docker Compose deployments, run:

```bash
./deployment/backup.sh
```

For Coolify, back up the persistent storage mounted at `/app/data`. Keep encrypted off-server copies and test restoration periodically.

## Upgrade

1. Back up `/app/data`.
2. Push the tested commit to `main`.
3. Let Coolify build and deploy the new image.
4. Check container health and logs.
5. Verify login, dashboard, assets, imports, and uploaded attachments.

The database and uploaded media survive image replacement because they are stored in the persistent volume.

## Troubleshooting

- Lost data after redeployment: confirm that Coolify storage is mounted at exactly `/app/data`.
- CSRF errors: use the complete `https://` origin in `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Disallowed host errors: add the hostname, without a scheme, to `DJANGO_ALLOWED_HOSTS`.
- Missing static styling: inspect startup logs for `collectstatic` errors.
- Unhealthy deployment: verify `/accounts/login/` returns HTTP 200 on port 8000.
- Permission errors: the image runs with the same simple root-container model used by RFdocker so Coolify-mounted storage remains writable.
