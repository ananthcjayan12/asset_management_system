# Asset Management System — Meeting Demo Script

This document is a simple narration guide for presenting the Asset Management System. Text in **bold brackets** is a presenter cue and does not need to be read aloud.

## Before the meeting

Install the demo dependencies once:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m playwright install chromium
```

Run the visible guided demo:

```bash
python e2e/run_demo.py
```

For a slower presentation:

```bash
python e2e/run_demo.py --action-pause-ms 2500 --slow-mo 900 --pause-ms 8000
```

The demo starts its own local Django server and uses an isolated SQLite database. It does not change the application's normal database. Temporary demo data is removed automatically after a successful run.

## Opening

**[Show the login screen.]**

“Good morning everyone. Today I will demonstrate our Asset Management System.

This application gives us one central place to manage the complete lifecycle of an organizational asset—from registration and procurement through installation, assignment, transfer, return, gate-pass movement, disposal, and reporting.

The system also provides QR-based asset identification, bulk Excel import, audit history, administrative master data, and role-based access control.

For this presentation, the software is using temporary demonstration data. The demo is isolated from the normal application database and will clean up its temporary records after it finishes.”

## 1. Dashboard

**[Sign in and show the dashboard.]**

“After signing in, we arrive at the dashboard. This gives us a quick summary of the asset register, including the total number of assets and their current statuses.

We can also see recent system activity and recent gate passes. The available menu options depend on the signed-in user's role and permissions.”

## 2. Asset register and search

**[Open Assets and use the search and status filters.]**

“The Asset Register is the main inventory of all organizational assets.

We can search for an asset using details such as its asset code, description, make, model, or serial number. We can also filter the list by its current status, such as In Stock, Assigned, Outside Premises, Under Disposal, or Disposed.

This allows users to find a specific asset quickly without manually checking spreadsheets or paper records.”

## 3. Asset details and QR identification

**[Open an asset, show its QR image, and open the QR page.]**

“Each asset has its own detailed record and a unique QR code.

The asset page shows its identification details, current status, location, custodian, procurement information, installation information, and movement history.

When an authorized user scans the QR code, the system opens the corresponding live asset page. This makes physical verification and asset identification much faster and reduces the risk of checking the wrong record.”

## 4. Editing and audit history

**[Edit the asset remarks and save.]**

“Authorized users can update an asset when its details change. For example, I can update the remarks and save the record.

Important actions are written to the audit history. This helps us identify what action was performed, when it happened, and which user performed it.”

## 5. Registering a new asset

**[Open the new asset form and move through its sections.]**

“We can register a complete asset using one structured workflow.

First, we enter the asset's core information, including its asset code, description, category, make, model, serial number, status, location, and custodian.

We can then record procurement details such as the supplier, purchase order, bill information, purchase date, and acquisition value.

Finally, we can add stock-entry, installation, commissioning, and warranty information. This keeps the operational and financial details connected to the same asset record.”

## 6. Asset transfer

**[Open Movements, select Transfer, and complete the transfer.]**

“The Movement module controls transfers between locations and custodians.

Here, we select an asset, its destination location, the receiving employee, the movement date, and the relevant reference details.

After the transfer is completed, the asset's current location and custodian are updated automatically. A permanent movement-history entry and transfer voucher are also created, giving us a clear chain of responsibility.”

## 7. Return to stock

**[Open Return to Stock and complete the return.]**

“When an employee returns an asset, we use the Return to Stock workflow.

We record the returning employee, the stores location, the date, and the reference number. The system then changes the asset status to In Stock and adds another entry to its movement history.

This means the current position of an asset and its complete historical trail are both retained.”

## 8. Temporary gate pass

**[Create a temporary pass, approve it, mark it outward, and then inward.]**

“The Gate Pass module manages assets that move outside the premises.

For a temporary gate pass, a user creates a request and records the asset, purpose, destination, carrier details, and expected return date.

The request then follows a controlled process: it is approved by Stores, marked outward by Security, and marked inward when the asset returns.

Once the item is received back, the pass is closed and the asset returns to its appropriate internal status. This provides clear accountability at every stage.”

## 9. Overdue gate-pass reporting

**[Create or show a temporary pass whose expected return date has passed.]**

“If a temporary gate pass remains open after its expected return date, the system identifies it as overdue.

This gives the responsible team a clear follow-up list and helps prevent assets from remaining outside the premises without attention.”

## 10. Permanent gate pass

**[Show a permanent pass being approved and marked outward.]**

“The system also supports permanent gate passes for assets that are not expected to return.

After approval and outward processing, the asset remains recorded as outside the premises. Unlike a temporary pass, a permanent pass does not provide an inward action. This prevents the two workflows from being confused.”

## 11. Disposal, write-off, and auction

**[Open Disposal, create a proposal, approve it, and show the final outcome.]**

“The Disposal module manages the final stage of the asset lifecycle.

An authorized user can create a disposal or write-off proposal. The proposal can then be reviewed and approved by a user with the correct authority.

Where an auction is involved, we can record details such as the lot, file number, auction identifier, successful buyer, and realized sale value.

When the process is finalized, the asset's status is updated to Disposed while its historical record remains available for audit and reporting.”

## 12. Bulk import from Excel

**[Open Imports, upload the workbook, show validation, and confirm.]**

“For initial data migration or bulk registration, the system supports Excel import.

The upload is staged before it changes the asset register. The system first validates the rows and presents a preview, allowing the user to review valid records and correct any errors.

Only after the user confirms the validated batch are the records added to the system. This two-stage process reduces the risk of importing incorrect or incomplete data.”

## 13. Verifying imported assets

**[Return to Assets and search for an imported asset code.]**

“After confirming the import, the new assets are immediately available in the searchable Asset Register.

They behave like manually entered records and can participate in the same transfer, gate-pass, return, disposal, QR, and reporting workflows.”

## 14. Reports and CSV export

**[Open Reports and download the CSV.]**

“The Reports screen provides a management-level view of the asset data.

It includes the total acquisition value, assets grouped by status, important location summaries, and overdue temporary gate passes.

The asset register can also be exported as a CSV file for further analysis, reconciliation, or sharing with authorized stakeholders.”

## 15. Administrative master data

**[Open Administration and show divisions, locations, employees, and suppliers.]**

“The administration area is used to maintain the master data that supports the operational workflows.

This includes organizational divisions, sections, subsections, locations, employees, and suppliers.

Maintaining these as controlled master records improves consistency. Users select approved values instead of repeatedly typing names and locations in different formats.”

## 16. Users, roles, and permissions

**[Open a user record and show its group assignment.]**

“Access to the system is controlled through users, roles, and permissions.

Available roles include Asset Administrators, Stores users, Division users, Approving Officers, Security users, Auditors, and Report Viewers.

Each role receives only the permissions needed for its responsibilities. For example, the person who creates a request does not automatically have every approval or security-processing permission.”

## 17. Report Viewer demonstration

**[Sign out as administrator and sign in as the report-viewer user.]**

“I will now sign in with a restricted Report Viewer account.

This user can view the permitted asset and reporting information, but administrative and operational actions are hidden. The user cannot create assets, perform transfers or returns, import data, or access system administration.

This demonstrates that permissions are enforced according to the user's assigned role.”

## 18. Final dashboard and summary

**[Return to the dashboard.]**

“We have now completed the main asset lifecycle in the system.

We registered and searched assets, used QR identification, updated a record, captured procurement and installation information, transferred and returned an asset, processed temporary and permanent gate passes, identified an overdue return, completed a disposal and auction workflow, imported assets from Excel, exported a report, and reviewed user permissions.

The dashboard now reflects the completed activities, and the recent activity log provides an audit trail of the demonstration.”

## Closing

“To summarize, this Asset Management System replaces disconnected records with a single, traceable process.

It helps the organization know what assets it owns, where each asset is located, who is responsible for it, how it was acquired, how it has moved, whether it has left the premises, and how it was finally disposed of.

The combination of structured workflows, role-based controls, QR identification, audit history, Excel import, and reporting improves visibility, accountability, and data quality throughout the asset lifecycle.

Thank you. I am happy to answer any questions.”

## Quick feature checklist

Use this section if someone asks what the software includes:

- Central asset register with search and status filters
- Asset description, make, model, serial number, specification, location, and custodian
- Procurement, supplier, purchase order, bill, value, and acquisition details
- Stock-entry, installation, commissioning, and warranty details
- QR code image and authenticated live asset page
- Asset editing with audit activity
- Transfers between locations and custodians
- Return-to-stock processing
- Movement history and transfer references
- Temporary gate passes with approval, outward, inward, and closure stages
- Overdue temporary gate-pass identification
- Permanent gate passes with controlled outward processing
- Disposal, write-off, approval, auction, buyer, and sale-value recording
- Staged Excel upload, validation preview, and confirmed bulk import
- Dashboard summaries and recent activity
- Asset status, location, acquisition-value, and overdue-pass reporting
- CSV export of the asset register
- Administrative master data for organizational units, locations, employees, and suppliers
- Role-based permissions for administrators, Stores, Divisions, Approvers, Security, Auditors, and Report Viewers
- Docker-based deployment support, backup examples, and local development mode
- Automated guided demo with screenshots, video, trace, logs, and reports

## Demo output files

After the guided demo completes, its files are saved under:

```text
e2e/artifacts/<timestamp>/
```

This folder includes the recorded browser video, screenshots, Playwright trace, server log, downloaded CSV, generated Excel workbook, and HTML/JSON reports.

The latest illustrated PDF guide is copied to:

```text
output/pdf/Asset_Management_UI_Demo_Guide.pdf
```
