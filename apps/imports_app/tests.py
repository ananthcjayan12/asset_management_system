from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from io import BytesIO
from openpyxl import Workbook
from apps.assets.models import Asset
from .models import ImportBatch
from datetime import date
from .services import confirm_batch, normalize_row, parse_date, validate_batch

class ImportTests(TestCase):
    def test_header_aliases(self):
        data = normalize_row({"Transaction ID": "T1", "Brief Description": "Laptop", "Room No": "10", "RFID Code": "R1", "Type of Inventory": "DIR"})
        self.assertEqual(data["TRANSACTION_ID"], "T1")
        self.assertEqual(data["BRIEF_DESCRIPTION"], "Laptop")
        self.assertEqual(data["ROOM_NO"], "10")
        self.assertEqual((data["ASSET_CODE"], data["INVENTORY_TYPE"]), ("R1", "DIR"))

    def test_parse_date_accepts_stored_excel_datetimes(self):
        self.assertEqual(parse_date("2026-07-01T00:00:00"), date(2026, 7, 1))
        self.assertEqual(parse_date("05-10-2026"), date(2026, 10, 5))

    def test_import_new_fields_accessories_and_auto_ids(self):
        wb = Workbook(); ws = wb.active
        ws.append(["RFID CODE", "TYPE OF INVENTORY", "BRIEF_DESCRIPTION", "MAIN ITEM", "CURRENCY", "AMOUNT", "DRR NO", "DRR DATE", "GRIN NO", "STATUS OF ASSET", "LOG BOOK MAINTAINED", "CENTRE", "BUILDING", "MAIN LOCATION", "ROOM NO"])
        ws.append(["RF-1", "PIR", "Computer", "", "EUR", 500, "DRR-9", "01-10-2026", "GRIN-9", "working", "yes", "RCED Kanpur", "Admin Block", "Lab", "12"])
        ws.append(["RF-2", "pir", "Monitor", "RF-1", "", "", "", "", "", "Not Working", "no", "RCED Kanpur", "Admin Block", "Lab", "12"])
        ws.append(["", "XYZ", "Bad row", "", "", "", "", "", "", "", "", "", "", "", ""])
        buffer = BytesIO(); wb.save(buffer)
        user = get_user_model().objects.create_user("importer")
        batch = ImportBatch.objects.create(uploaded_file=SimpleUploadedFile("t.xlsx", buffer.getvalue()), uploaded_by=user)
        validate_batch(batch)
        self.assertEqual((batch.valid_rows, batch.invalid_rows), (2, 1))
        batch.rows.filter(validation_status="INVALID").delete(); batch.invalid_rows = 0; batch.save()
        confirm_batch(batch, user)
        computer, monitor = Asset.objects.get(asset_code="RF-1"), Asset.objects.get(asset_code="RF-2")
        self.assertEqual(monitor.parent_asset, computer)
        self.assertEqual((computer.inventory_type, monitor.inventory_type), ("PIR", "PIR"))
        self.assertTrue(computer.transaction_id and computer.sl_no)
        self.assertEqual((computer.procurement.currency, computer.procurement.drr_no), ("EUR", "DRR-9"))
        self.assertEqual((computer.installation.status_of_asset, computer.installation.log_book_maintained), ("Working", True))
        self.assertEqual(monitor.installation.status_of_asset, "Not working")
        self.assertEqual((str(computer.current_location.building), computer.current_location.room_no), ("Admin Block (RCED Kanpur)", "12"))
        self.assertEqual(computer.current_location.place.name, "Lab")
