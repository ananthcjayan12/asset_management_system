#!/usr/bin/env python3
"""Run a visible, end-to-end Playwright tour of the asset system.

The default mode is intentionally safe:
- only localhost is allowed;
- a dedicated SQLite database is created under e2e/artifacts;
- temporary users and records use the PWDEMO prefix;
- successful runs clean their temporary application data;
- failures keep the database and browser artifacts for debugging.
"""
from __future__ import annotations

import argparse
import csv
import json
import html
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests
from openpyxl import Workbook
from playwright.sync_api import Browser, BrowserContext, Locator, Page, Playwright, expect, sync_playwright
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
E2E_ROOT = PROJECT_ROOT / "e2e"
DEFAULT_ARTIFACTS_ROOT = E2E_ROOT / "artifacts"
PREFIX = "PWDEMO"
ADMIN_USERNAME = "pw_demo_admin"
ADMIN_PASSWORD = "PlaywrightAdmin123!"
VIEWER_USERNAME = "pw_demo_viewer"
VIEWER_PASSWORD = "PlaywrightViewer123!"

STEP_DETAILS: dict[str, list[str]] = {
    "Administrator dashboard and activity summary": [
        "Sign in with the temporary administrator account.",
        "Review asset totals, current status counters, recent activity and recent gate passes.",
        "Confirm that the administrator navigation exposes all application modules.",
    ],
    "Asset register search and status filtering": [
        "Open Assets from the main navigation.",
        "Search by make and apply the Issued status filter.",
        "Confirm that the baseline demonstration asset remains visible.",
    ],
    "Authenticated QR webpage and QR image endpoint": [
        "Open the baseline asset record and verify its QR image endpoint.",
        "Open the authenticated QR landing page.",
        "Confirm the QR page resolves to the correct asset.",
    ],
    "Asset edit and audit-producing update": [
        "Open the asset edit form and change its remarks.",
        "Save the record and verify the success message.",
        "The update is written to the application's audit activity.",
    ],
    "Register a complete asset with procurement and installation": [
        "Create an asset with an optional RFID code, PIR/DIR/IIR type, status, location and custodian.",
        "Add procurement data including currency, unit rate, PO, bill, DRR and GRIN details.",
        "Add stock-entry, installation, working status and log book details; SL No. and Transaction ID are generated on save.",
    ],
    "Accessory registered as a sub-part of the main item": [
        "Use Add accessory on the main item to register a monitor with its own serial number.",
        "The form is pre-filled from the main item (type, location, custodian).",
        "The accessory is listed under the main item's Accessories section.",
    ],
    "Transfer workflow and movement history": [
        "Open Movements and choose Transfer; search for the asset and review its details panel.",
        "Move the asset and its accessory to the demo lab, assign a recipient and change PIR to DIR.",
        "Verify the transferred date, the recorded changes and the accessory's new location.",
    ],
    "Return-to-stock workflow and second movement record": [
        "Open Return to stock for the transferred asset.",
        "Record the returned stock location, return-from name, voucher and the Surplus return clause.",
        "Verify In stock status and the second movement-history entry.",
    ],
    "Temporary gate pass: request, Stores approval, outward and inward": [
        "Create a temporary gate pass for the UI-created asset using the asset search box.",
        "Demonstrate the controlled sequence: request, division approval, Stores approval and security outward.",
        "Mark the asset inward and confirm the pass closes and the asset returns to stock.",
    ],
    "Overdue temporary gate pass left outward for reporting": [
        "Create a temporary gate pass with an expected return date in the past.",
        "Approve it and mark it outward.",
        "Leave it open so the Reports screen can identify it as overdue.",
    ],
    "Permanent gate pass remains outward with no inward action": [
        "Create and approve a permanent gate pass.",
        "Mark the asset outward.",
        "Confirm there is no inward button and the asset remains outside the premises.",
    ],
    "Gate pass rejected with a reason": [
        "Create another gate-pass request.",
        "Reject it at the division-approval stage with a reason.",
        "The pass shows Rejected with who rejected it and why; Stores can also reject after division approval.",
    ],
    "Stores returns tab with return clause": [
        "Open Disposal and switch to the Stores returns tab.",
        "Returned items are listed with their Surplus / Obsolete / Unserviceable clause.",
        "Only Stores can classify returned items into disposal lots.",
    ],
    "Disposal proposal, approval and auction final outcome": [
        "Create and save a disposal record for the prepared disposal asset.",
        "Approve the proposal using the authorized account.",
        "Record auction details and confirm the asset's final Disposed status.",
    ],
    "Excel upload, validation preview and confirmed bulk import": [
        "Upload the generated two-row asset workbook.",
        "Review the validation result before changing application data.",
        "Confirm the batch and verify both valid rows are imported.",
    ],
    "Imported asset verified in the searchable register": [
        "Return to the asset register.",
        "Search for one of the newly imported asset codes.",
        "Confirm that the imported record is available through the UI.",
    ],
    "Physical verification of assets": [
        "Open Verification and choose Record verification.",
        "List the assets expected at the demo office and mark each Available or Not available.",
        "Review the verification report with date-range and result filters.",
    ],
    "Reports, overdue pass visibility and CSV export": [
        "Review acquisition value per currency, assets by status, PIR/DIR/IIR and top locations.",
        "Confirm the overdue temporary gate pass is listed.",
        "Download the asset-register CSV and verify key demonstration assets are included.",
    ],
    "Date-wise PIR/DIR report grouped by division": [
        "Open Asset reports and choose a date range, the PIR/DIR type and a Division-wise report.",
        "Reports are also available employee-wise, room-wise, location-wise, building-wise and centre-wise.",
        "The same filters apply to the CSV download.",
    ],
    "Employee master with year-wise calendar": [
        "Open Add employee in Administration.",
        "Date of joining and date of retirement are recorded for each employee.",
        "The calendar sits beside the date and offers month and year drop-downs for quick year-wise navigation.",
    ],
    "Administration master data: divisions, locations, employees and suppliers": [
        "Open Django Administration with the administrator account.",
        "Review the prepared division, locations, employees and supplier.",
        "Confirm that operational forms are backed by maintained master data.",
    ],
    "Administration user and role assignment": [
        "Search for the temporary report-viewer user.",
        "Open the user and verify membership in the Report Viewer group.",
        "This demonstrates role-based permission assignment.",
    ],
    "Report Viewer role sees data but not administrator actions": [
        "Sign out as administrator and sign in as the report-viewer user.",
        "Verify data screens remain accessible.",
        "Confirm create, transfer, return, import and administration actions are hidden.",
    ],
    "Final dashboard with the complete temporary audit trail": [
        "Return to the dashboard after completing all workflows.",
        "Review the updated counters and recent activity.",
        "The isolated demonstration data is cleaned automatically after a successful run.",
    ],
}


@dataclass
class DemoReport:
    started_at: float = field(default_factory=time.time)
    steps: list[dict] = field(default_factory=list)
    console_messages: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    status: str = "running"
    error: str = ""
    current_step: str = ""

    def add_step(
        self,
        number: int,
        title: str,
        screenshot: Path,
        notes: list[str],
        actions: list[str],
    ) -> None:
        self.current_step = title
        self.steps.append({
            "number": number,
            "title": title,
            "screenshot": str(screenshot),
            "notes": notes,
            "actions": actions,
            "timestamp": time.time(),
        })

    def save(self, path: Path) -> None:
        payload = {
            "status": self.status,
            "error": self.error,
            "current_step": self.current_step,
            "duration_seconds": round(time.time() - self.started_at, 2),
            "steps": self.steps,
            "console_messages": self.console_messages,
            "page_errors": self.page_errors,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def save_html(self, path: Path) -> None:
        cards = []
        for step in self.steps:
            screenshot = Path(step["screenshot"])
            try:
                screenshot_ref = screenshot.relative_to(path.parent)
            except ValueError:
                screenshot_ref = screenshot
            title = html.escape(step["title"])
            ref = html.escape(screenshot_ref.as_posix())
            notes = "".join(f"<li>{html.escape(note)}</li>" for note in step.get("notes", []))
            actions = "".join(f"<li>{html.escape(note)}</li>" for note in step.get("actions", []))
            cards.append(
                f'<section><h2>{step["number"]:02d}. {title}</h2>'
                f"<ol>{notes}</ol>"
                f"<h3>On-screen actions</h3><ol>{actions}</ol>"
                f'<a href="{ref}"><img src="{ref}" alt="{title}"></a></section>'
            )
        error_block = f'<pre>{html.escape(self.error)}</pre>' if self.error else ""
        document = (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Playwright asset-management feature tour</title>'
            '<style>body{font-family:system-ui,sans-serif;max-width:1180px;margin:0 auto;padding:24px;background:#f5f7fb;color:#172033}'
            'header,section{background:white;border:1px solid #dfe5ef;border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 4px 16px rgba(18,38,63,.06)}'
            'img{max-width:100%;height:auto;border:1px solid #dfe5ef;border-radius:8px}.status{font-weight:700;text-transform:uppercase}'
            'pre{white-space:pre-wrap;color:#991b1b}</style></head><body>'
            '<header><h1>Asset-management guided feature tour</h1>'
            f'<p class="status">Status: {html.escape(self.status)}</p>'
            f'<p>Completed checkpoints: {len(self.steps)}</p>{error_block}</header>'
            + ''.join(cards)
            + '</body></html>'
        )
        path.write_text(document, encoding="utf-8")

    def save_pdf(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        page_size = landscape(A4)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DemoTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172033"),
            spaceAfter=10,
        )
        step_style = ParagraphStyle(
            "StepTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#172033"),
            spaceAfter=7,
        )
        note_style = ParagraphStyle(
            "StepNote",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#344054"),
            spaceAfter=3,
        )
        story = [
            Spacer(1, 42 * mm),
            Paragraph("Asset Management System", title_style),
            Paragraph("Detailed Guided UI Demonstration", title_style),
            Spacer(1, 8 * mm),
            Paragraph(
                f"{len(self.steps)} verified workflows with explanations and captured application screens.",
                ParagraphStyle("Subtitle", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=13, leading=18),
            ),
            Spacer(1, 12 * mm),
            Paragraph(
                "Generated from the isolated Playwright demonstration. Temporary data is used so the ordinary application database is not affected.",
                ParagraphStyle("CoverNote", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=10, leading=14),
            ),
            PageBreak(),
        ]
        for index, step in enumerate(self.steps):
            story.append(Paragraph(f'{step["number"]:02d}. {html.escape(step["title"])}', step_style))
            for note in step.get("notes", []):
                story.append(Paragraph(f"- {html.escape(note)}", note_style))
            actions = step.get("actions", [])
            if actions:
                story.append(Paragraph("On-screen actions", ParagraphStyle(
                    "ActionHeading",
                    parent=styles["Heading2"],
                    fontName="Helvetica-Bold",
                    fontSize=10,
                    leading=12,
                    textColor=colors.HexColor("#0B5ED7"),
                    spaceBefore=2,
                    spaceAfter=2,
                )))
                for action_number, action in enumerate(actions, start=1):
                    story.append(Paragraph(f"{action_number}. {html.escape(action)}", note_style))
            story.append(Spacer(1, 3 * mm))
            screenshot = Path(step["screenshot"])
            if screenshot.exists():
                screenshot_on_separate_page = len(actions) > 4
                if screenshot_on_separate_page:
                    story.append(PageBreak())
                    story.append(Paragraph(
                        f'{step["number"]:02d}. {html.escape(step["title"])} - Screen capture',
                        step_style,
                    ))
                    story.append(Paragraph(
                        "Verified application state after completing the actions described on the preceding page.",
                        note_style,
                    ))
                    story.append(Spacer(1, 3 * mm))
                image = PdfImage(str(screenshot))
                max_width = 245 * mm
                max_height = (142 if screenshot_on_separate_page else 92) * mm
                scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
                image.drawWidth = image.imageWidth * scale
                image.drawHeight = image.imageHeight * scale
                image.hAlign = "CENTER"
                story.append(image)
            if index < len(self.steps) - 1:
                story.append(PageBreak())

        def footer(canvas, document) -> None:
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#D0D5DD"))
            canvas.line(18 * mm, 12 * mm, page_size[0] - 18 * mm, 12 * mm)
            canvas.setFillColor(colors.HexColor("#667085"))
            canvas.setFont("Helvetica", 8)
            canvas.drawString(18 * mm, 7 * mm, "Asset Management System - Guided UI Demonstration")
            canvas.drawRightString(page_size[0] - 18 * mm, 7 * mm, f"Page {document.page}")
            canvas.restoreState()

        document = SimpleDocTemplate(
            str(path),
            pagesize=page_size,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=14 * mm,
            bottomMargin=16 * mm,
            title="Asset Management System - Detailed Guided UI Demonstration",
            author="Asset Management System",
        )
        document.build(story, onFirstPage=footer, onLaterPages=footer)


class Tour:
    def __init__(self, *, artifacts_dir: Path, pause_ms: int, action_pause_ms: int, report: DemoReport, headless: bool):
        self.artifacts_dir = artifacts_dir
        self.pause_ms = 0 if headless else pause_ms
        self.action_pause_ms = 0 if headless else action_pause_ms
        self.report = report
        self.step_number = 0
        self.pending_actions: list[str] = []

    def checkpoint(
        self,
        page: Page,
        title: str,
        *,
        assertion: Callable[[], None] | None = None,
        full_page: bool = True,
    ) -> None:
        if assertion:
            assertion()
        self.step_number += 1
        safe = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70]
        screenshot = self.artifacts_dir / "screenshots" / f"{self.step_number:02d}-{safe}.png"
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        page.evaluate("document.getElementById('pw-demo-action')?.remove()")
        notes = STEP_DETAILS.get(title, [])
        self._show_banner(page, f"Checkpoint {self.step_number}: {title}")
        page.screenshot(path=str(screenshot), full_page=full_page)
        self.report.add_step(self.step_number, title, screenshot, notes, list(self.pending_actions))
        self.pending_actions.clear()
        print(f"[{self.step_number:02d}] {title}")
        if self.pause_ms:
            page.wait_for_timeout(self.pause_ms)
        self._hide_banner(page)

    def action(self, page: Page, note: str) -> None:
        page.evaluate(
            """note => {
                document.getElementById('pw-demo-action')?.remove();
                const banner = document.createElement('div');
                banner.id = 'pw-demo-action';
                banner.innerHTML = '<div style="font-size:12px;opacity:.75;margin-bottom:4px">NEXT ACTION</div>' +
                    '<div></div>';
                banner.lastElementChild.textContent = note;
                Object.assign(banner.style, {
                    position: 'fixed', left: '20px', bottom: '20px', zIndex: '2147483647',
                    background: '#0b5ed7', color: '#fff', padding: '13px 18px',
                    borderRadius: '10px', boxShadow: '0 8px 24px rgba(0,0,0,.3)',
                    font: '600 16px system-ui, sans-serif', maxWidth: '52vw',
                    pointerEvents: 'none'
                });
                document.body.appendChild(banner);
            }""",
            note,
        )
        print(f"     -> {note}")
        self.pending_actions.append(note)
        if self.action_pause_ms:
            page.wait_for_timeout(self.action_pause_ms)

    @staticmethod
    def _show_banner(page: Page, title: str) -> None:
        page.evaluate(
            """title => {
                document.getElementById('pw-demo-banner')?.remove();
                const banner = document.createElement('div');
                banner.id = 'pw-demo-banner';
                banner.textContent = title;
                Object.assign(banner.style, {
                    position: 'fixed', top: '14px', right: '14px', zIndex: '2147483647',
                    background: '#111827', color: '#fff', padding: '12px 18px',
                    borderRadius: '10px', boxShadow: '0 8px 24px rgba(0,0,0,.3)',
                    font: '600 16px system-ui, sans-serif', maxWidth: '48vw'
                });
                document.body.appendChild(banner);
            }""",
            title,
        )

    @staticmethod
    def _hide_banner(page: Page) -> None:
        page.evaluate("document.getElementById('pw-demo-banner')?.remove()")
        page.evaluate("document.getElementById('pw-demo-action')?.remove()")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the complete Playwright feature demonstration.")
    parser.add_argument("--headless", action="store_true", help="Run without showing the browser window.")
    parser.add_argument("--slow-mo", type=int, default=650, help="Delay every Playwright action by this many milliseconds.")
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=5000,
        help="Pause after each narrated feature checkpoint (default: 5000 ms for a live demo).",
    )
    parser.add_argument(
        "--action-pause-ms",
        type=int,
        default=1800,
        help="Show each NEXT ACTION note for this long before clicking (default: 1800 ms).",
    )
    parser.add_argument("--port", type=int, default=8000, help="Local development server port.")
    parser.add_argument("--artifacts-dir", type=Path, help="Directory for screenshots, trace, video, logs and report.")
    parser.add_argument("--keep-data", action="store_true", help="Keep temporary database records after a successful run.")
    parser.add_argument("--keep-database", action="store_true", help="Keep the isolated SQLite database after a successful run.")
    parser.add_argument("--reuse-database", action="store_true", help="Reuse the existing isolated SQLite database file.")
    parser.add_argument("--use-running-server", action="store_true", help="Do not start Django; use --base-url instead.")
    parser.add_argument("--base-url", default="", help="Application URL when using an already-running server.")
    parser.add_argument("--use-configured-database", action="store_true", help="Use current database environment instead of isolated SQLite.")
    parser.add_argument("--allow-remote", action="store_true", help="Allow a non-localhost base URL. Use only on a disposable test system.")
    return parser.parse_args()


def new_run_directory(root: Path | None) -> Path:
    if root:
        run_dir = root.resolve()
    else:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        run_dir = (DEFAULT_ARTIFACTS_ROOT / stamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def is_local_url(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}


def port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True


def demo_environment(args: argparse.Namespace, run_dir: Path) -> tuple[dict[str, str], Path | None]:
    env = os.environ.copy()
    env.update({
        "DJANGO_DEBUG": "True",
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "DJANGO_SECRET_KEY": "playwright-local-demo-only-secret-key",
        "QR_PAGE_PUBLIC": "False",
        "PYTHONUNBUFFERED": "1",
    })
    database_path: Path | None = None
    if not args.use_configured_database:
        for key in list(env):
            if key.startswith("MYSQL_"):
                env.pop(key, None)
        database_path = run_dir / "playwright-demo.sqlite3"
        env["SQLITE_DATABASE_PATH"] = str(database_path)
    return env, database_path


def manage(env: dict[str, str], *arguments: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(PROJECT_ROOT / "manage.py"), *arguments]
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        check=True,
        capture_output=capture,
    )


def wait_for_server(base_url: str, process: subprocess.Popen[str] | None, timeout: int = 40) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        if process and process.poll() is not None:
            raise RuntimeError(f"Django server exited with code {process.returncode}.")
        try:
            response = requests.get(f"{base_url}/accounts/login/", timeout=1.5, allow_redirects=True)
            if response.status_code < 500:
                return
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.35)
    raise RuntimeError(f"Django server did not become ready: {last_error}")


def start_server(env: dict[str, str], port: int, run_dir: Path) -> tuple[subprocess.Popen[str], str, object]:
    if not port_is_available(port):
        raise RuntimeError(f"Port {port} is already in use. Stop that service or pass --port with a free port.")
    log_handle = (run_dir / "django-server.log").open("w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "manage.py"), "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        wait_for_server(base_url, process)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        log_handle.close()
        raise
    return process, base_url, log_handle


def launch_browser(playwright: Playwright, *, headless: bool, slow_mo: int) -> Browser:
    launch_args = {"headless": headless, "slow_mo": slow_mo, "args": ["--no-sandbox"]}
    try:
        return playwright.chromium.launch(**launch_args)
    except Exception as first_error:
        candidates = [
            os.getenv("PW_BROWSER_PATH", ""),
            shutil.which("chromium") or "",
            shutil.which("chromium-browser") or "",
            shutil.which("google-chrome") or "",
            shutil.which("msedge") or "",
        ]
        for executable in candidates:
            if executable:
                try:
                    return playwright.chromium.launch(executable_path=executable, **launch_args)
                except Exception:
                    continue
        raise RuntimeError(
            "Chromium could not be launched. Run `python -m playwright install chromium` "
            "or set PW_BROWSER_PATH to an installed Chromium executable."
        ) from first_error


def make_import_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Asset Import"
    headers = [
        "ASSET_CODE", "TRANSACTION_ID", "BRIEF_DESCRIPTION", "SPECIFICATION", "MAKE", "MODEL",
        "ITEM_SL_NO", "QTY", "AMOUNT", "PO_NO", "SUPPLIER_NAME", "STATUS_OF_ASSET", "ROOM_NO",
        "EMP_ID", "EMP_NAME", "DIVISION", "SECTION", "MAIN_LOCATION", "REMARKS",
    ]
    sheet.append(headers)
    sheet.append([
        "PWDEMO-IMP-001", "PWDEMO-TX-IMP-001", "Imported demo monitor", "27-inch display",
        "Automation Make", "Import Model A", "SN-PWDEMO-IMP-001", 1, 18000, "PO-PWDEMO-IMP-001",
        "PW Demo Supplier", "ASSIGNED", "PW-101", "PWEMP001", "Playwright Demo Custodian",
        "Playwright Demo Division", "Automation Section", "PW Demo Office", "PWDEMO import row one",
    ])
    sheet.append([
        "PWDEMO-IMP-002", "PWDEMO-TX-IMP-002", "Imported demo printer", "Network laser printer",
        "Automation Make", "Import Model B", "SN-PWDEMO-IMP-002", 1, 32000, "PO-PWDEMO-IMP-002",
        "PW Demo Supplier", "IN_STOCK", "PW-ST-01", "", "",
        "Playwright Demo Division", "Automation Section", "PW Demo Central Stores", "PWDEMO import row two",
    ])
    sheet.freeze_panes = "A2"
    workbook.save(path)


def narrated_click(page: Page, tour: Tour, locator: Locator, note: str) -> None:
    tour.action(page, note)
    locator.click()


def login(page: Page, base_url: str, username: str, password: str, tour: Tour) -> None:
    page.goto(f"{base_url}/accounts/login/", wait_until="networkidle")
    tour.action(page, f"Enter the credentials for {username}.")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(password)
    narrated_click(page, tour, page.get_by_role("button", name="Sign in"), "Sign in and open the dashboard.")
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()


def sign_out(page: Page, tour: Tour) -> None:
    narrated_click(page, tour, page.get_by_role("button", name="Sign out"), "Sign out of the administrator account.")
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()


def click_nav(page: Page, tour: Tour, name: str) -> None:
    narrated_click(page, tour, page.get_by_role("link", name=name, exact=True), f"Open the {name} module.")
    page.wait_for_load_state("networkidle")


def select_asset_checkbox(page: Page, tour: Tour, asset_code: str) -> None:
    label = page.locator("label", has_text=asset_code).first
    expect(label).to_be_visible()
    narrated_click(page, tour, label, f"Select asset {asset_code} for this gate pass.")


def create_gatepass(
    page: Page,
    tour: Tour,
    *,
    asset_code: str,
    gatepass_type: str,
    purpose: str,
    destination: str,
    expected_return: date | None,
) -> None:
    click_nav(page, tour, "Gate Passes")
    narrated_click(page, tour, page.get_by_role("link", name="Request gate pass"), "Start a new gate-pass request.")
    tour.action(page, f"Enter the {gatepass_type.lower()} gate-pass details and expected destination.")
    page.locator("#id_gatepass_type").select_option(gatepass_type)
    page.locator("#id_division").select_option(label="PWDEMO - Playwright Demo Division")
    page.locator("#id_purpose").fill(purpose)
    page.locator("#id_destination").fill(destination)
    if expected_return:
        page.locator("#id_expected_return_date").fill(expected_return.isoformat())
    page.locator("#asset-search").fill(asset_code)
    select_asset_checkbox(page, tour, asset_code)
    page.locator("#id_remarks").fill("PWDEMO automated feature tour")
    narrated_click(page, tour, page.get_by_role("button", name="Submit request"), "Submit the gate pass for division and Stores approval.")
    expect(page.locator(".text-muted")).to_contain_text("Requested")


def approve_and_mark_outward(page: Page, tour: Tour) -> None:
    narrated_click(page, tour, page.get_by_role("button", name="Division approve"), "Approve the request as the division admin.")
    expect(page.locator(".alert")).to_contain_text("approved by the division")
    narrated_click(page, tour, page.get_by_role("button", name="Stores approve"), "Approve the division-approved gate pass as Stores.")
    expect(page.locator(".alert")).to_contain_text("approved by Stores")
    narrated_click(page, tour, page.get_by_role("button", name="Mark outward"), "Record the security outward movement.")
    expect(page.locator(".alert")).to_contain_text("marked outward")


def run_feature_tour(page: Page, context: BrowserContext, base_url: str, tour: Tour, import_path: Path, run_dir: Path) -> None:
    today = date.today()
    ui_asset_code = "PWDEMO-UI-001"
    ui_accessory_code = "PWDEMO-UI-ACC-001"

    login(page, base_url, ADMIN_USERNAME, ADMIN_PASSWORD, tour)
    tour.checkpoint(
        page,
        "Administrator dashboard and activity summary",
        assertion=lambda: expect(page.get_by_text("Total assets", exact=True)).to_be_visible(),
    )

    click_nav(page, tour, "Assets")
    tour.action(page, "Search the asset register by make and filter it to Issued assets.")
    search = page.locator('input[name="q"]')
    search.fill("Automation Make")
    expect(page.get_by_role("link", name="PWDEMO-BASE-001")).to_be_visible()
    page.locator('select[name="status"]').select_option("ASSIGNED")
    expect(page.get_by_role("link", name="PWDEMO-BASE-001")).to_be_visible()
    tour.checkpoint(page, "Asset register search and status filtering")

    narrated_click(page, tour, page.get_by_role("link", name="PWDEMO-BASE-001"), "Open the baseline asset record.")
    expect(page.get_by_text("Baseline laptop for search and QR demonstration")).to_be_visible()
    qr_href = page.get_by_role("link", name="QR PNG").get_attribute("href")
    assert qr_href
    qr_response = page.request.get(f"{base_url}{qr_href}")
    assert qr_response.ok and qr_response.headers.get("content-type", "").startswith("image/png")
    narrated_click(page, tour, page.get_by_role("link", name="Open QR page"), "Open the asset page represented by the QR code.")
    expect(page.get_by_text("PWDEMO-BASE-001", exact=True)).to_be_visible()
    tour.checkpoint(page, "Authenticated QR webpage and QR image endpoint")
    page.go_back(wait_until="networkidle")

    narrated_click(page, tour, page.get_by_role("link", name="Edit"), "Open the asset edit form.")
    tour.action(page, "Update the remarks so the change appears in the audit trail.")
    page.locator("#id_remarks").fill("PWDEMO remarks updated by the Playwright feature tour.")
    narrated_click(page, tour, page.get_by_role("button", name="Save asset"), "Save the asset update.")
    expect(page.get_by_text("Asset updated successfully.")).to_be_visible()
    expect(page.get_by_text("PWDEMO remarks updated by the Playwright feature tour.")).to_be_visible()
    tour.checkpoint(page, "Asset edit and audit-producing update")

    click_nav(page, tour, "Assets")
    narrated_click(page, tour, page.get_by_role("link", name="Register asset"), "Open the complete asset-registration form.")
    tour.action(page, "Enter the optional RFID code, type of inventory, specification, status, location and custodian.")
    page.locator("#id_asset_code").fill(ui_asset_code)
    page.locator("#id_inventory_type").select_option("PIR")
    page.locator("#id_brief_description").fill("Playwright UI registered laptop")
    page.locator("#id_specification").fill("16 GB RAM, 512 GB SSD; temporary demo data")
    page.locator("#id_make").fill("Automation Make")
    page.locator("#id_model").fill("UI Model")
    page.locator("#id_item_sl_no").fill("SN-PWDEMO-UI-001")
    page.locator("#id_current_status").select_option("ASSIGNED")
    page.locator("#id_current_location").select_option(label="PW Demo Office / PW-101")
    page.locator("#id_current_custodian").select_option(label="PWEMP001 - Playwright Demo Custodian")
    page.locator("#id_room_in_charge_name").fill("Playwright Demo Officer")
    page.locator("#id_current_user").fill("Playwright Demo Custodian")
    page.locator("#id_remarks").fill("PWDEMO created through the asset registration UI")

    narrated_click(page, tour, page.get_by_role("button", name="Procurement", exact=True), "Expand the procurement section.")
    tour.action(page, "Enter quantity, currency, unit rate, purchase order, supplier, bill, DRR and GRIN information.")
    page.locator("#id_proc-qty").fill("1")
    page.locator("#id_proc-currency").select_option("INR")
    page.locator("#id_proc-amount").fill("65000")
    page.locator("#id_proc-po_no").fill("PO-PWDEMO-UI-001")
    page.locator("#id_proc-po_date").fill(today.isoformat())
    page.locator("#id_proc-supplier").select_option(label="PW Demo Supplier")
    page.locator("#id_proc-bill_no").fill("BILL-PWDEMO-UI-001")
    page.locator("#id_proc-bill_date").fill(today.isoformat())
    page.locator("#id_proc-bill_value").fill("65000")
    page.locator("#id_proc-drr_no").fill("DRR-PWDEMO-UI-001")
    page.locator("#id_proc-drr_date").fill(today.strftime("%d-%m-%Y"))
    page.locator("#id_proc-grin_no").fill("GRIN-PWDEMO-UI-001")
    page.locator("#id_proc-grin_date").fill(today.strftime("%d-%m-%Y"))

    narrated_click(page, tour, page.get_by_role("button", name="Stock and installation"), "Expand the stock and installation section.")
    tour.action(page, "Enter the stock-entry reference, installation date, warranty, working status and log book.")
    page.locator("#id_install-stock_entry_reference").fill("SE-PWDEMO-UI-001")
    page.locator("#id_install-date_of_installation").fill(today.isoformat())
    page.locator("#id_install-warranty_period_months").fill("36")
    page.locator("#id_install-status_of_asset").select_option("Working")
    page.locator("#id_install-log_book_maintained").select_option("true")
    narrated_click(page, tour, page.get_by_role("button", name="Save asset"), "Save the complete asset record.")
    expect(page.get_by_text("Asset created successfully.")).to_be_visible()
    expect(page.get_by_role("heading", name=ui_asset_code)).to_be_visible()
    expect(page.locator("dl").get_by_text("PIR", exact=True)).to_be_visible()
    tour.checkpoint(page, "Register a complete asset with procurement and installation")

    narrated_click(page, tour, page.get_by_role("link", name="Add accessory").first, "Register a monitor as an accessory of this computer.")
    tour.action(page, "The accessory form is pre-filled from the main item; enter the monitor's own details and serial number.")
    page.locator("#id_asset_code").fill(ui_accessory_code)
    page.locator("#id_brief_description").fill("Playwright UI accessory monitor")
    page.locator("#id_make").fill("Automation Make")
    page.locator("#id_item_sl_no").fill("SN-PWDEMO-UI-ACC-001")
    narrated_click(page, tour, page.get_by_role("button", name="Save asset"), "Save the accessory.")
    expect(page.get_by_text("Asset created successfully.")).to_be_visible()
    narrated_click(page, tour, page.locator("dl").get_by_role("link", name=ui_asset_code), "Open the main item to see its accessories.")
    expect(page.get_by_role("link", name=ui_accessory_code)).to_be_visible()
    tour.checkpoint(page, "Accessory registered as a sub-part of the main item")

    click_nav(page, tour, "Movements")
    narrated_click(page, tour, page.get_by_role("link", name="Transfer"), "Open the asset-transfer workflow.")
    tour.action(page, "Search for the asset, review its details, then choose destination, recipient, PIR/DIR change, voucher and transferred date.")
    page.get_by_role("searchbox", name="Search Asset").fill(ui_asset_code)
    expect(page.locator("#asset-summary")).to_contain_text("Playwright UI accessory monitor")
    page.locator("#id_destination").select_option(label="PW Demo Lab / PW-202")
    page.locator("#id_recipient").select_option(label="PWEMP002 - Playwright Demo Recipient")
    page.locator("#id_inventory_type").select_option("DIR")
    page.locator("#id_voucher_number").fill("PWDEMO-TRANS-001")
    page.locator("#id_movement_date").fill(today.isoformat())
    page.locator("#id_remarks").fill("PWDEMO UI transfer")
    narrated_click(page, tour, page.get_by_role("button", name="Execute transfer"), "Execute the transfer and update the asset's custody.")
    # The location also appears in movement history. Scope these checks to the
    # asset-details definition list so Playwright has exactly one match.
    expect(page.locator("dl").get_by_text("PW Demo Lab / PW-202", exact=True)).to_be_visible()
    expect(page.locator("dl").get_by_text("PWEMP002 - Playwright Demo Recipient", exact=True)).to_be_visible()
    expect(page.get_by_text("PWDEMO-TRANS-001")).to_be_visible()
    expect(page.get_by_text("PIR/DIR: PIR \u2192 DIR")).to_be_visible()
    expect(page.locator("tr", has_text=ui_accessory_code)).to_contain_text("PW Demo Lab / PW-202")
    tour.checkpoint(page, "Transfer workflow and movement history")

    click_nav(page, tour, "Movements")
    narrated_click(page, tour, page.get_by_role("link", name="Return to stock"), "Open the return-to-stock workflow.")
    tour.action(page, "Choose the returned stock location, return-from name, voucher and return clause.")
    page.locator("#id_asset").select_option(label=f"{ui_asset_code} - Playwright UI registered laptop")
    page.locator("#id_stock_location").select_option(label="PW Demo Central Stores / PW-ST-01")
    page.locator("#id_returned_by").select_option(label="PWEMP002 - Playwright Demo Recipient")
    page.locator("#id_voucher_number").fill("PWDEMO-RETURN-001")
    page.locator("#id_movement_date").fill(today.isoformat())
    page.locator("#id_return_clause").select_option("Surplus")
    page.locator("#id_remarks").fill("PWDEMO UI return")
    narrated_click(page, tour, page.get_by_role("button", name="Record return"), "Record the return and restore the asset to stock.")
    expect(page.locator("dl").get_by_text("In stock", exact=True)).to_be_visible()
    expect(page.locator("dl").get_by_text("PW Demo Central Stores / PW-ST-01", exact=True)).to_be_visible()
    expect(page.get_by_text("PWDEMO-RETURN-001")).to_be_visible()
    tour.checkpoint(page, "Return-to-stock workflow and second movement record")

    create_gatepass(
        page,
        tour,
        asset_code=ui_asset_code,
        gatepass_type="TEMPORARY",
        purpose="PWDEMO temporary equipment service",
        destination="Automation Service Centre",
        expected_return=today + timedelta(days=7),
    )
    approve_and_mark_outward(page, tour)
    narrated_click(page, tour, page.get_by_role("button", name="Mark inward"), "Record the asset's inward return and close the temporary pass.")
    expect(page.locator(".text-muted")).to_contain_text("Closed")
    expect(page.get_by_text("Out: Yes | In: Yes")).to_be_visible()
    narrated_click(page, tour, page.get_by_role("link", name=ui_asset_code), "Open the asset and verify it returned to stock.")
    expect(page.locator("dl").get_by_text("In stock", exact=True)).to_be_visible()
    expect(page.locator("dl").get_by_text("PW Demo Central Stores / PW-ST-01", exact=True)).to_be_visible()
    tour.checkpoint(page, "Temporary gate pass: request, Stores approval, outward and inward")

    create_gatepass(
        page,
        tour,
        asset_code="PWDEMO-OVERDUE-001",
        gatepass_type="TEMPORARY",
        purpose="PWDEMO overdue reporting scenario",
        destination="External Calibration Centre",
        expected_return=today - timedelta(days=5),
    )
    approve_and_mark_outward(page, tour)
    tour.checkpoint(page, "Overdue temporary gate pass left outward for reporting")

    create_gatepass(
        page,
        tour,
        asset_code="PWDEMO-PERM-001",
        gatepass_type="PERMANENT",
        purpose="PWDEMO permanent removal from premises",
        destination="Permanent Recipient",
        expected_return=None,
    )
    approve_and_mark_outward(page, tour)
    expect(page.locator(".alert")).to_contain_text("marked outward")
    expect(page.get_by_role("button", name="Mark inward")).to_have_count(0)
    narrated_click(page, tour, page.get_by_role("link", name="PWDEMO-PERM-001"), "Open the permanent-pass asset to verify its Outside status.")
    expect(page.get_by_text("Outside premises", exact=True)).to_be_visible()
    tour.checkpoint(page, "Permanent gate pass remains outward with no inward action")

    create_gatepass(
        page,
        tour,
        asset_code="PWDEMO-BASE-001",
        gatepass_type="PERMANENT",
        purpose="PWDEMO request to be rejected",
        destination="Not approved",
        expected_return=None,
    )
    narrated_click(page, tour, page.get_by_role("button", name="Reject"), "Open the rejection panel.")
    page.locator("#id_reason").fill("PWDEMO item is still required in the division")
    narrated_click(page, tour, page.get_by_role("button", name="Confirm rejection"), "Reject the gate pass with a reason.")
    expect(page.locator(".alert-danger")).to_contain_text("PWDEMO item is still required in the division")
    tour.checkpoint(page, "Gate pass rejected with a reason")

    click_nav(page, tour, "Disposal")
    narrated_click(page, tour, page.get_by_role("link", name="Stores returns"), "Open the Stores returns tab.")
    page.locator("#clause").select_option("Surplus")
    page.wait_for_load_state("networkidle")
    expect(page.locator("tr", has_text=ui_asset_code)).to_contain_text("Surplus")
    tour.checkpoint(page, "Stores returns tab with return clause")

    click_nav(page, tour, "Disposal")
    narrated_click(page, tour, page.get_by_role("link", name="Disposal records"), "Return to the disposal records tab.")
    narrated_click(page, tour, page.get_by_role("link", name="New record"), "Start a new disposal record.")
    tour.action(page, "Select the disposal asset and enter lot, file and book-value information.")
    page.locator("#id_asset").select_option(label="PWDEMO-DISP-001 - Asset for disposal and auction demonstration")
    page.locator("#id_lot_name").fill("PWDEMO Lot 01")
    page.locator("#id_disposal_file_no").fill("PWDEMO-DISP-FILE-001")
    page.locator("#id_total_book_value").fill("25000")
    page.locator("#id_financial_year").fill("2026-27")
    page.locator("#id_remarks").fill("PWDEMO disposal proposal")
    narrated_click(page, tour, page.get_by_role("button", name="Save", exact=True), "Save the disposal record in Proposed status.")
    row = page.locator("tr", has_text="PWDEMO-DISP-001")
    expect(row.get_by_text("Proposed", exact=True)).to_be_visible()
    narrated_click(page, tour, row.get_by_role("link", name="Edit"), "Open the proposal for authorized approval.")
    page.locator("#id_status").select_option("APPROVED")
    narrated_click(page, tour, page.get_by_role("button", name="Save changes"), "Approve the disposal proposal.")
    row = page.locator("tr", has_text="PWDEMO-DISP-001")
    expect(row.get_by_text("Approved", exact=True)).to_be_visible()
    narrated_click(page, tour, row.get_by_role("link", name="Edit"), "Open the approved record to enter the auction outcome.")
    tour.action(page, "Enter auction ID, buyer and realized sale values.")
    page.locator("#id_status").select_option("AUCTIONED")
    page.locator("#id_auction_id").fill("PWDEMO-AUCTION-001")
    page.locator("#id_h1_buyer").fill("PW Demo Buyer")
    page.locator("#id_realized_sale_value").fill("17500")
    page.locator("#id_apportioned_sale_value").fill("17500")
    narrated_click(page, tour, page.get_by_role("button", name="Save changes"), "Save the auction result and finalize the asset as Disposed.")
    row = page.locator("tr", has_text="PWDEMO-DISP-001")
    expect(row.get_by_text("Auctioned", exact=True)).to_be_visible()
    narrated_click(page, tour, row.get_by_role("link", name="PWDEMO-DISP-001"), "Open the asset to verify its final Disposed status.")
    expect(page.get_by_text("Disposed", exact=True)).to_be_visible()
    tour.checkpoint(page, "Disposal proposal, approval and auction final outcome")

    click_nav(page, tour, "Import")
    narrated_click(page, tour, page.get_by_role("link", name="Upload workbook"), "Open the bulk-import upload form.")
    tour.action(page, "Attach the generated Excel workbook and add a batch note.")
    page.locator("#id_uploaded_file").set_input_files(str(import_path))
    page.locator("#id_notes").fill("PWDEMO generated workbook for the Playwright feature tour")
    narrated_click(page, tour, page.get_by_role("button", name="Upload and validate"), "Upload the workbook and validate every row.")
    expect(page.get_by_text("2 valid / 0 invalid")).to_be_visible()
    narrated_click(page, tour, page.get_by_role("button", name="Confirm import"), "Confirm the validated batch and create the assets.")
    expect(page.get_by_text("Imported 2 assets.")).to_be_visible()
    expect(page.locator("h1 + div")).to_contain_text("Completed")
    tour.checkpoint(page, "Excel upload, validation preview and confirmed bulk import")

    click_nav(page, tour, "Assets")
    tour.action(page, "Search for one newly imported asset code.")
    page.locator('input[name="q"]').fill("PWDEMO-IMP-001")
    expect(page.get_by_role("link", name="PWDEMO-IMP-001")).to_be_visible()
    tour.checkpoint(page, "Imported asset verified in the searchable register")

    click_nav(page, tour, "Verification")
    narrated_click(page, tour, page.get_by_role("link", name="Record verification"), "Start a physical verification.")
    tour.action(page, "Choose the demo office and list the assets expected there.")
    page.locator("#id_location").select_option(label="PW Demo Office / PW-101")
    narrated_click(page, tour, page.get_by_role("button", name="List assets"), "List the assets expected at this location.")
    narrated_click(page, tour, page.get_by_role("button", name="Mark all available"), "Mark every listed asset as available.")
    overdue_row = page.locator("tr", has_text="PWDEMO-OVERDUE-001")
    overdue_row.get_by_label("Not available").check()
    overdue_row.get_by_role("textbox").fill("PWDEMO out for calibration")
    narrated_click(page, tour, page.get_by_role("button", name="Save verification"), "Save the verification results.")
    expect(page.get_by_text("Saved verification for")).to_be_visible()
    expect(page.locator("tr", has_text="PWDEMO-OVERDUE-001")).to_contain_text("Not available")
    tour.checkpoint(page, "Physical verification of assets")

    click_nav(page, tour, "Reports")
    expect(page.get_by_text("Acquisition value", exact=True)).to_be_visible()
    expect(page.get_by_text("PWDEMO overdue reporting scenario")).to_be_visible()
    with page.expect_download() as download_info:
        narrated_click(page, tour, page.get_by_role("link", name="Download asset register CSV"), "Download the complete asset register as CSV.")
    download = download_info.value
    csv_path = run_dir / "asset-register.csv"
    download.save_as(str(csv_path))
    assert csv_path.exists() and csv_path.stat().st_size > 0
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        exported_codes = {row[2] for row in csv.reader(csv_file) if len(row) > 2}
    assert {"PWDEMO-BASE-001", "PWDEMO-IMP-001", ui_asset_code}.issubset(exported_codes)
    tour.checkpoint(page, "Reports, overdue pass visibility and CSV export")

    narrated_click(page, tour, page.get_by_role("link", name="Asset reports (date-wise, PIR/DIR)"), "Open the configurable asset reports.")
    tour.action(page, "Choose a Division-wise PIR report for this month's registrations.")
    page.locator("#id_group_by").select_option("division")
    page.locator("#id_inventory_type").select_option("PIR")
    page.locator("#id_date_from").fill(today.replace(day=1).strftime("%d-%m-%Y"))
    page.locator("#id_date_to").fill(today.strftime("%d-%m-%Y"))
    narrated_click(page, tour, page.get_by_role("button", name="Generate"), "Generate the report.")
    expect(page.get_by_text("Division-wise summary")).to_be_visible()
    expect(page.locator("tr", has_text="Playwright Demo Division").first).to_be_visible()
    tour.checkpoint(page, "Date-wise PIR/DIR report grouped by division")

    click_nav(page, tour, "Administration")
    expect(page.get_by_role("heading", name="Site administration")).to_be_visible()
    tour.action(page, "Review the prepared master data used by operational workflows.")
    page.goto(f"{base_url}/admin/core/division/", wait_until="networkidle")
    expect(page.get_by_text("Playwright Demo Division")).to_be_visible()
    page.goto(f"{base_url}/admin/core/location/", wait_until="networkidle")
    expect(page.get_by_text("PW Demo Central Stores")).to_be_visible()
    expect(page.get_by_text("PW Demo Office")).to_be_visible()
    page.goto(f"{base_url}/admin/core/employee/", wait_until="networkidle")
    expect(page.get_by_text("Playwright Demo Custodian")).to_be_visible()
    page.goto(f"{base_url}/admin/core/supplier/", wait_until="networkidle")
    expect(page.get_by_text("PW Demo Supplier")).to_be_visible()
    tour.checkpoint(page, "Administration master data: divisions, locations, employees and suppliers")

    page.goto(f"{base_url}/admin/core/employee/add/", wait_until="networkidle")
    narrated_click(page, tour, page.locator("#id_date_of_joining + .dp-toggle"), "Open the calendar beside Date of joining.")
    page.locator(".dp-popup .dp-year").select_option(str(today.year - 10))
    expect(page.locator(".dp-popup")).to_be_visible()
    tour.checkpoint(page, "Employee master with year-wise calendar", full_page=False)

    page.goto(f"{base_url}/admin/auth/user/", wait_until="networkidle")
    page.locator("#searchbar").fill(VIEWER_USERNAME)
    narrated_click(page, tour, page.locator('input[type="submit"][value="Search"]'), "Search for the prepared report-viewer user.")
    expect(page.get_by_role("link", name=VIEWER_USERNAME)).to_be_visible()
    narrated_click(page, tour, page.get_by_role("link", name=VIEWER_USERNAME), "Open the user and inspect the assigned role.")
    expect(page.locator("#id_groups_to")).to_contain_text("Report Viewer")
    page.locator("#id_groups_to").scroll_into_view_if_needed()
    tour.checkpoint(page, "Administration user and role assignment", full_page=False)

    page.goto(f"{base_url}/", wait_until="networkidle")
    sign_out(page, tour)
    login(page, base_url, VIEWER_USERNAME, VIEWER_PASSWORD, tour)
    expect(page.get_by_role("link", name="Administration")).to_have_count(0)
    expect(page.get_by_role("link", name="Import", exact=True)).to_have_count(0)
    click_nav(page, tour, "Assets")
    expect(page.get_by_role("link", name="Register asset")).to_have_count(0)
    click_nav(page, tour, "Movements")
    expect(page.get_by_role("link", name="Transfer")).to_have_count(0)
    expect(page.get_by_role("link", name="Return to stock")).to_have_count(0)
    click_nav(page, tour, "Disposal")
    expect(page.get_by_role("link", name="New record")).to_have_count(0)
    tour.checkpoint(page, "Report Viewer role sees data but not administrator actions")

    page.goto(f"{base_url}/", wait_until="networkidle")
    tour.checkpoint(
        page,
        "Final dashboard with the complete temporary audit trail",
        assertion=lambda: expect(page.get_by_role("heading", name="Dashboard")).to_be_visible(),
    )


def main() -> int:
    args = parse_args()
    run_dir = new_run_directory(args.artifacts_dir)
    report = DemoReport()
    report_path = run_dir / "demo-report.json"
    pdf_path = run_dir / "Asset_Management_UI_Demo_Guide.pdf"
    published_pdf_path = PROJECT_ROOT / "output" / "pdf" / "Asset_Management_UI_Demo_Guide.pdf"
    env, database_path = demo_environment(args, run_dir)
    server_process: subprocess.Popen[str] | None = None
    server_log_handle = None
    context: BrowserContext | None = None
    browser: Browser | None = None
    success = False

    if args.use_running_server:
        if not args.base_url:
            raise SystemExit("--use-running-server requires --base-url.")
        base_url = args.base_url.rstrip("/")
        if not args.allow_remote and not is_local_url(base_url):
            raise SystemExit("Remote URLs are blocked by default. Use --allow-remote only for a disposable test environment.")
        if not args.use_configured_database:
            raise SystemExit("--use-running-server also requires --use-configured-database so commands target the same database.")
    else:
        base_url = f"http://127.0.0.1:{args.port}"

    try:
        print(f"Artifacts: {run_dir}")
        if database_path and database_path.exists() and not args.reuse_database:
            database_path.unlink()

        manage(env, "migrate", "--noinput")
        prepared = manage(env, "prepare_playwright_demo", "--json", capture=True)
        (run_dir / "prepared-data.json").write_text(prepared.stdout, encoding="utf-8")
        import_path = run_dir / "pwdemo-import.xlsx"
        make_import_workbook(import_path)

        if args.use_running_server:
            wait_for_server(base_url, None)
        else:
            server_process, base_url, server_log_handle = start_server(env, args.port, run_dir)

        with sync_playwright() as playwright:
            browser = launch_browser(playwright, headless=args.headless, slow_mo=args.slow_mo)
            context = browser.new_context(
                viewport={"width": 1440, "height": 960},
                accept_downloads=True,
                record_video_dir=str(run_dir / "video"),
                record_video_size={"width": 1440, "height": 960},
            )
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()
            page.set_default_timeout(18000)
            page.on("console", lambda message: report.console_messages.append(f"{message.type}: {message.text}") if message.type in {"warning", "error"} else None)
            page.on("pageerror", lambda error: report.page_errors.append(str(error)))

            tour = Tour(
                artifacts_dir=run_dir,
                pause_ms=args.pause_ms,
                action_pause_ms=args.action_pause_ms,
                report=report,
                headless=args.headless,
            )
            run_feature_tour(page, context, base_url, tour, import_path, run_dir)
            report.status = "passed"
            success = True
            context.tracing.stop(path=str(run_dir / "playwright-trace.zip"))

    except Exception as exc:
        report.status = "failed"
        report.error = f"{type(exc).__name__}: {exc}"
        (run_dir / "failure-traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        if context:
            try:
                pages = context.pages
                if pages:
                    pages[-1].screenshot(path=str(run_dir / "failure.png"), full_page=True)
                context.tracing.stop(path=str(run_dir / "playwright-trace.zip"))
            except Exception:
                pass
        print(f"FAILED during: {report.current_step or 'setup'}", file=sys.stderr)
        print(report.error, file=sys.stderr)
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        if server_process:
            server_process.terminate()
            try:
                server_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server_process.kill()
        if server_log_handle:
            server_log_handle.close()

        # Keep failure state automatically. Successful runs clean unless requested otherwise.
        if success and not args.keep_data:
            try:
                manage(env, "cleanup_playwright_demo", "--json", capture=True)
            except Exception as cleanup_error:
                report.console_messages.append(f"Cleanup error: {cleanup_error}")
        if success and database_path and not args.keep_database:
            try:
                database_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                report.console_messages.append(f"Database cleanup error: {cleanup_error}")

        report.save(report_path)
        report.save_html(run_dir / "demo-report.html")
        if report.steps:
            report.save_pdf(pdf_path)
            if success:
                published_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(pdf_path, published_pdf_path)

    if success:
        print(f"PASS: complete feature tour finished. Report: {report_path}")
        print(f"Detailed PDF guide: {published_pdf_path}")
        print(f"Open trace: python -m playwright show-trace {run_dir / 'playwright-trace.zip'}")
        return 0
    print(f"Failure artifacts preserved in {run_dir}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
