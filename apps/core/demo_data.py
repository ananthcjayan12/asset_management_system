"""Temporary data helpers used by the local Playwright feature tour.

All records created here use the PWDEMO prefix so cleanup is deterministic and
cannot remove ordinary application data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from apps.assets.models import Asset, Installation, Procurement
from apps.core.models import AuditEvent, Division, Employee, Location, Section, Supplier
from apps.core.roles import ensure_groups
from apps.disposal.models import DisposalRecord
from apps.gatepasses.models import GatePass
from apps.imports_app.models import ImportBatch
from apps.movements.models import AssetMovement

PREFIX = "PWDEMO"
ADMIN_USERNAME = "pw_demo_admin"
ADMIN_PASSWORD = "PlaywrightAdmin123!"
VIEWER_USERNAME = "pw_demo_viewer"
VIEWER_PASSWORD = "PlaywrightViewer123!"

def _create_asset(*, code: str, tx: str, description: str, location: Location, custodian: Employee, supplier: Supplier) -> Asset:
    asset, _ = Asset.objects.update_or_create(
        asset_code=code,
        defaults={
            "transaction_id": tx,
            "inventory_type": Asset.InventoryType.PIR,
            "brief_description": description,
            "specification": "Playwright temporary demonstration asset",
            "make": "Automation Make",
            "model": "Tour Model",
            "item_sl_no": f"SN-{code}",
            "current_status": Asset.Status.ASSIGNED,
            "current_location": location,
            "current_custodian": custodian,
            "room_in_charge_name": "Playwright Demo Officer",
            "current_user": custodian.name,
            "remarks": "Temporary data created by the Playwright demo suite.",
            "is_active": True,
        },
    )
    Procurement.objects.update_or_create(
        asset=asset,
        defaults={
            "qty": 1,
            "amount": 25000,
            "po_no": f"PO-{code}",
            "supplier": supplier,
            "bill_no": f"BILL-{code}",
            "bill_value": 25000,
        },
    )
    Installation.objects.update_or_create(
        asset=asset,
        defaults={
            "stock_entry_reference": f"SE-{code}",
            "warranty_period_months": 24,
            "status_of_asset": "Working",
        },
    )
    return asset


@transaction.atomic
def prepare_demo_data(
    *,
    admin_username: str = ADMIN_USERNAME,
    admin_password: str = ADMIN_PASSWORD,
    viewer_username: str = VIEWER_USERNAME,
    viewer_password: str = VIEWER_PASSWORD,
) -> dict[str, Any]:
    ensure_groups()
    User = get_user_model()

    admin, _ = User.objects.update_or_create(
        username=admin_username,
        defaults={"email": "pw-demo-admin@example.local", "is_staff": True, "is_superuser": True, "is_active": True},
    )
    admin.set_password(admin_password)
    admin.save(update_fields=["password"])

    viewer, _ = User.objects.update_or_create(
        username=viewer_username,
        defaults={"email": "pw-demo-viewer@example.local", "is_staff": False, "is_superuser": False, "is_active": True},
    )
    viewer.set_password(viewer_password)
    viewer.save(update_fields=["password"])
    viewer.groups.set([Group.objects.get(name="Report Viewer")])

    division, _ = Division.objects.update_or_create(
        code=PREFIX,
        defaults={"name": "Playwright Demo Division"},
    )
    section, _ = Section.objects.get_or_create(division=division, name="Automation Section")
    stock, _ = Location.objects.update_or_create(
        name="PW Demo Central Stores",
        room_no="PW-ST-01",
        defaults={"division": division, "section": section, "is_stock_location": True, "is_active": True},
    )
    office, _ = Location.objects.update_or_create(
        name="PW Demo Office",
        room_no="PW-101",
        defaults={"division": division, "section": section, "is_stock_location": False, "is_active": True},
    )
    lab, _ = Location.objects.update_or_create(
        name="PW Demo Lab",
        room_no="PW-202",
        defaults={"division": division, "section": section, "is_stock_location": False, "is_active": True},
    )
    custodian, _ = Employee.objects.update_or_create(
        employee_id="PWEMP001",
        defaults={"name": "Playwright Demo Custodian", "division": division, "section": section, "is_active": True},
    )
    recipient, _ = Employee.objects.update_or_create(
        employee_id="PWEMP002",
        defaults={"name": "Playwright Demo Recipient", "division": division, "section": section, "is_active": True},
    )
    supplier, _ = Supplier.objects.update_or_create(
        name="PW Demo Supplier",
        defaults={"contact_person": "Automation Contact", "email": "pw-demo-supplier@example.local"},
    )

    assets = {
        "baseline": _create_asset(
            code="PWDEMO-BASE-001", tx="PWDEMO-TX-BASE-001",
            description="Baseline laptop for search and QR demonstration",
            location=office, custodian=custodian, supplier=supplier,
        ),
        "permanent": _create_asset(
            code="PWDEMO-PERM-001", tx="PWDEMO-TX-PERM-001",
            description="Asset for permanent gate-pass demonstration",
            location=office, custodian=custodian, supplier=supplier,
        ),
        "disposal": _create_asset(
            code="PWDEMO-DISP-001", tx="PWDEMO-TX-DISP-001",
            description="Asset for disposal and auction demonstration",
            location=lab, custodian=custodian, supplier=supplier,
        ),
        "overdue": _create_asset(
            code="PWDEMO-OVERDUE-001", tx="PWDEMO-TX-OVERDUE-001",
            description="Asset for overdue temporary gate-pass reporting",
            location=office, custodian=custodian, supplier=supplier,
        ),
    }

    return {
        "prefix": PREFIX,
        "admin": {"username": admin_username, "password": admin_password},
        "viewer": {"username": viewer_username, "password": viewer_password},
        "division": str(division),
        "stock_location": str(stock),
        "office_location": str(office),
        "lab_location": str(lab),
        "custodian": str(custodian),
        "recipient": str(recipient),
        "supplier": str(supplier),
        "assets": {key: asset.asset_code for key, asset in assets.items()},
    }


@transaction.atomic
def cleanup_demo_data(*, delete_users: bool = True) -> dict[str, int]:
    """Delete only records identified by the PWDEMO prefix."""
    counts: dict[str, int] = {}

    batches = list((
        ImportBatch.objects.filter(notes__icontains=PREFIX)
        | ImportBatch.objects.filter(uploaded_file__icontains="pwdemo")
    ).distinct())
    for batch in batches:
        if batch.uploaded_file:
            batch.uploaded_file.delete(save=False)
    counts["import_batches"] = len(batches)
    ImportBatch.objects.filter(pk__in=[batch.pk for batch in batches]).delete()

    assets = Asset.objects.filter(asset_code__startswith=PREFIX)
    asset_ids = list(assets.values_list("pk", flat=True))

    gatepasses = GatePass.objects.filter(purpose__startswith=PREFIX)
    counts["gatepasses"] = gatepasses.count()
    gatepasses.delete()

    counts["disposals"] = DisposalRecord.objects.filter(asset_id__in=asset_ids).count()
    DisposalRecord.objects.filter(asset_id__in=asset_ids).delete()
    counts["movements"] = AssetMovement.objects.filter(asset_id__in=asset_ids).count()
    AssetMovement.objects.filter(asset_id__in=asset_ids).delete()

    counts["assets"] = assets.count()
    assets.delete()

    counts["audit_events"] = AuditEvent.objects.filter(description__icontains=PREFIX).count()
    AuditEvent.objects.filter(description__icontains=PREFIX).delete()

    if delete_users:
        User = get_user_model()
        users = User.objects.filter(username__in=[ADMIN_USERNAME, VIEWER_USERNAME])
        counts["users"] = users.count()
        users.delete()

    Supplier.objects.filter(name="PW Demo Supplier", procurements__isnull=True).delete()
    Employee.objects.filter(employee_id__startswith="PWEMP", assets__isnull=True).delete()
    Location.objects.filter(name__startswith="PW Demo", assets__isnull=True).delete()
    Section.objects.filter(division__code=PREFIX, locations__isnull=True, employees__isnull=True).delete()
    Division.objects.filter(code=PREFIX, locations__isnull=True, employees__isnull=True, gatepasses__isnull=True).delete()

    return counts
