# Add guided Playwright feature tour and strengthen workflow permissions

## Summary

- Add a one-command Playwright guided demo covering dashboard, asset search/detail/QR/edit/create, transfers, returns, temporary and permanent gate passes, overdue reporting, disposal/auction, Excel import, CSV export, administration and role restrictions.
- Create isolated deterministic `PWDEMO-*` data plus temporary administrator/report-viewer users through management commands.
- Generate screenshots, video, trace, Django server log, generated Excel workbook, downloaded CSV, and JSON/HTML reports.
- Add a GitHub Actions workflow for Django tests and the headless browser tour.
- Keep successful runs clean while preserving failure state for debugging.

## Fixes included

- Keep permanent gate passes in `OUTWARD` state after security outward scanning.
- Prevent inward processing for permanent gate passes.
- Hide navigation and action controls from users without the matching permission.
- Expose a direct QR webpage link from the asset detail page.

## Test plan

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
python -m unittest e2e.test_run_demo
python manage.py check
python manage.py test
python e2e/run_demo.py --headless --pause-ms 0 --slow-mo 0
```

For the visible guided demo:

```bash
python e2e/run_demo.py
```
