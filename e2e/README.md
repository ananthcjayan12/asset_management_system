# Playwright guided feature tour

This suite is both a visual product demonstration and a repeatable debugging tool. It creates a temporary administrator, a restricted report-viewer user, master data and a small set of `PWDEMO-*` assets. It then drives the browser through the main workflows and produces screenshots, video, a Playwright trace, server logs, the generated Excel workbook, a downloaded CSV and a JSON report.

## Install once

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m playwright install chromium
```

## Run the visible demonstration

```bash
python e2e/run_demo.py
```

The visible run is presentation-paced:

- every click is preceded by a blue **NEXT ACTION** explanation;
- the explanation remains visible for 1.8 seconds before the click;
- every browser action has a 650 ms slow-motion delay;
- every numbered checkpoint remains on screen for 5 seconds;
- the completed run creates a detailed PDF with all 18 explanations and screenshots.

Increase the timing for a slower presentation:

```bash
# 2.5-second action notes, 900 ms per action and 8-second checkpoints
python e2e/run_demo.py --action-pause-ms 2500 --slow-mo 900 --pause-ms 8000
```

The runner starts an isolated local SQLite database and Django development server automatically. It does not use the ordinary `db.sqlite3` or MySQL configuration unless explicitly requested.

Useful modes:

```bash
# CI or quick debugging (no presentation pauses)
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0

# Keep successful demo records and the isolated database for manual inspection
python e2e/run_demo.py --keep-data --keep-database

# Use a different local port
python e2e/run_demo.py --port 8010
```

Artifacts are written to `e2e/artifacts/<timestamp>/`. To inspect a trace:

```bash
python -m playwright show-trace e2e/artifacts/<timestamp>/playwright-trace.zip
```

The latest successful illustrated guide is also copied to:

```text
output/pdf/Asset_Management_UI_Demo_Guide.pdf
```

## Safety

By default the runner only accepts localhost, forces a dedicated SQLite file, deletes temporary data after success, and preserves the database on failure. Remote execution requires explicit `--allow-remote --use-running-server --use-configured-database` flags and should only target a disposable test environment.
