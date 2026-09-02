# Playwright guided demo validation

## Scope

The change adds a self-contained guided browser tour for the asset-management application. It creates only records with the `PWDEMO` prefix, uses a dedicated SQLite database by default, and generates screenshots, video, a Playwright trace, server logs, CSV and Excel files, plus JSON and HTML reports.

## Automated checks performed in the implementation environment

### Passed

```text
python -m compileall -q .
Result: PASS
```

```text
python -m unittest -v e2e.test_run_demo
Result: PASS (5 tests)
```

The unit checks cover the localhost safety guard, isolated SQLite environment, generated two-row Excel workbook, JSON/HTML report generation, and the required UI-selector contract.

A Chromium smoke test was also executed successfully with Playwright using `/usr/bin/chromium`. It validated browser launch, role selectors and screenshot creation.

### Full Django/Playwright execution attempt

```text
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0
```

The runner reached its setup stage and correctly attempted `python manage.py migrate`. The implementation environment did not contain Django, and its configured Python package proxy returned HTTP 503 for Django and related packages, so the application server could not be started here. The failure was preserved in the runner's normal debugging artifacts.

This is an environment dependency limitation rather than a passing end-to-end result. The included GitHub Actions workflow installs the declared dependencies and runs:

```text
python -m unittest e2e.test_run_demo
python manage.py check
python manage.py test
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0
```

The full browser result should therefore be treated as pending until the workflow runs in GitHub or the suite is run in a local virtual environment with `requirements-dev.txt` installed.

## Bugs fixed while building the tour

1. Permanent gate passes now remain in `Marked outward` state after the outward scan and do not expose an inward action.
2. Main navigation and gate-pass creation actions are hidden when the signed-in user lacks the required permission.
3. A regression test verifies that a permanent gate pass cannot be marked inward.
4. Temporary demo cleanup is prefix-scoped and has a test proving that ordinary assets are retained.

## Recommended acceptance command

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
python manage.py test
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0
```

For a visible narrated demonstration, omit the three speed/headless arguments:

```bash
python e2e/run_demo.py
```
