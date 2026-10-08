from datetime import date
from unittest import mock
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.core.models import Division, Employee, Location
from .models import Asset, AssetVerification

class AssetModelTests(TestCase):
    def test_asset_gets_unique_qr_token(self):
        a = Asset.objects.create(asset_code="A1", transaction_id="T1", brief_description="Test")
        self.assertIsNotNone(a.qr_token)
        self.assertEqual(str(a), "A1 - Test")

    def test_serial_and_transaction_id_are_generated(self):
        with mock.patch("apps.assets.models.timezone.localdate", return_value=date(2026, 10, 7)):
            first = Asset.objects.create(brief_description="First")
            second = Asset.objects.create(brief_description="Second")
        self.assertEqual((first.transaction_id, second.transaction_id), ("07-10-2026-0001", "07-10-2026-0002"))
        self.assertEqual(second.sl_no, first.sl_no + 1)

    def test_rfid_code_is_optional_and_display_falls_back_to_transaction_id(self):
        a = Asset.objects.create(asset_code="", brief_description="No tag yet")
        b = Asset.objects.create(brief_description="Also untagged")
        self.assertIsNone(a.asset_code)
        self.assertEqual(b.display_code, b.transaction_id)

    def test_division_defaults_from_custodian(self):
        div = Division.objects.create(code="D", name="Division")
        emp = Employee.objects.create(employee_id="E1", name="Emp", division=div)
        self.assertEqual(Asset.objects.create(brief_description="X", current_custodian=emp).division, div)

class AssetViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", password="x")
        self.client.force_login(self.user)
        self.location = Location.objects.create(name="Lab", room_no="1")

    def test_register_asset_with_dd_mm_yyyy_dates_and_new_fields(self):
        response = self.client.post("/assets/new/", {
            "inventory_type": "DIR", "brief_description": "Computer", "nc_date": "05-10-2026",
            "current_status": "IN_STOCK", "current_location": self.location.pk, "is_active": "on",
            "proc-qty": "1", "proc-currency": "USD", "proc-amount": "100", "proc-bill_value": "100",
            "proc-drr_no": "DRR-1", "proc-drr_date": "06-10-2026", "proc-grin_no": "GRIN-1",
            "install-status_of_asset": "Not working", "install-log_book_maintained": "true",
        })
        self.assertEqual(response.status_code, 302, getattr(response, "context", {}) and [f.errors for f in (response.context["asset_form"], response.context["procurement_form"], response.context["installation_form"])])
        asset = Asset.objects.get(brief_description="Computer")
        self.assertEqual(asset.nc_date, date(2026, 10, 5))
        self.assertEqual((asset.procurement.currency, asset.procurement.drr_date), ("USD", date(2026, 10, 6)))
        self.assertEqual((asset.installation.status_of_asset, asset.installation.log_book_maintained), ("Not working", True))
        self.assertIsNone(asset.asset_code)

    def test_inventory_type_is_required(self):
        response = self.client.post("/assets/new/", {"brief_description": "X", "current_status": "IN_STOCK", "proc-qty": "1", "proc-currency": "INR"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("inventory_type", response.context["asset_form"].errors)

    def test_accessory_prefills_from_main_item(self):
        main = Asset.objects.create(brief_description="Computer", inventory_type="PIR", current_location=self.location)
        response = self.client.get(f"/assets/new/?parent={main.pk}")
        self.assertEqual(response.context["asset_form"].initial["parent_asset"], main.pk)
        self.assertContains(response, "Add accessory to")

    def test_bulk_verification(self):
        a = Asset.objects.create(brief_description="A", current_location=self.location)
        b = Asset.objects.create(brief_description="B", current_location=self.location)
        url = f"/assets/verification/record/?location={self.location.pk}&verification_date=07-10-2026"
        self.assertContains(self.client.get(url), a.display_code)
        self.client.post(url, {f"result_{a.pk}": "AVAILABLE", f"result_{b.pk}": "NOT_AVAILABLE", f"remarks_{b.pk}": "Missing"})
        self.assertEqual(AssetVerification.objects.get(asset=b).remarks, "Missing")
        report = self.client.get("/assets/verification/?result=NOT_AVAILABLE&date_from=01-10-2026&date_to=31-10-2026")
        self.assertContains(report, "Missing")
        self.assertNotContains(report, f">{a.display_code}<")
