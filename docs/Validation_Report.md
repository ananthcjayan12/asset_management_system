# Validation Report

## Completed in the build environment

- Python source and committed migrations compiled successfully with `python -m compileall`.
- Docker entrypoint, backup and restore scripts passed POSIX shell syntax checks.
- `docker-compose.yml` parsed successfully and contains the expected `web` and `db` services.
- The IIS reverse-proxy example parsed successfully as XML.
- The project tree was checked for missing referenced files and unwanted runtime artefacts.
- The Docker entrypoint refuses production-mode startup while example secrets or passwords remain in `.env`.
- The Excel import template was created and inspected with `artifact_tool`; headers, example data, date formatting and dropdown validation were verified.
- The DOCX manual was rendered to PDF and 15 PNG pages. Every rendered page was visually reviewed for clipping, overlapping, split table rows, headers and footers.
- The original supplied requirements document is included under `docs/` for traceability.

## Must be completed in the target environment

The build environment does not provide a Docker engine or the full Python runtime dependencies, so the following commands must be run on the deployment/staging host:

```bash
docker compose build --pull
docker compose up -d
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py check --deploy
```

Then execute user-acceptance tests for manual registration, Excel import, transfer, return, temporary gate pass, permanent gate pass, disposal/write-off/passout, QR scanning, CSV export, permissions, backup and restore.

This package is a working starter implementation, not a substitute for organisation-specific UAT, security assessment, data cleansing, process approval and operational ownership.
