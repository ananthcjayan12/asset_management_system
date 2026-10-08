from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.assets.models import Asset
from apps.core.models import Division, Employee, Location
from .services import transfer_asset, return_asset
class MovementServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("approver", password="x")
        self.div = Division.objects.create(code="D", name="Division")
        self.stock = Location.objects.create(name="Stock", room_no="1", division=self.div, is_stock_location=True)
        self.office = Location.objects.create(name="Office", room_no="2", division=self.div)
        self.emp = Employee.objects.create(employee_id="E1", name="Employee", division=self.div)
        self.asset = Asset.objects.create(asset_code="A1", transaction_id="T1", brief_description="Test", current_location=self.stock)
    def test_transfer_then_return(self):
        transfer_asset(asset=self.asset, destination=self.office, recipient=self.emp, approved_by=self.user)
        self.asset.refresh_from_db(); self.assertEqual(self.asset.current_location, self.office); self.assertEqual(self.asset.current_custodian, self.emp)
        return_asset(asset=self.asset, stock_location=self.stock, returned_by=self.emp, approved_by=self.user)
        self.asset.refresh_from_db(); self.assertEqual(self.asset.current_location, self.stock); self.assertIsNone(self.asset.current_custodian); self.assertEqual(self.asset.current_status, Asset.Status.IN_STOCK)

    def test_transfer_records_changes_and_moves_accessories(self):
        from apps.core.models import Building, Centre
        other_div = Division.objects.create(code="D2", name="Other Division")
        building = Building.objects.create(name="Main Block", centre=Centre.objects.get(name="RCED Kolkata"))
        lab = Location.objects.create(name="Lab", room_no="9", building=building, division=other_div)
        self.asset.inventory_type = "PIR"; self.asset.save()
        monitor = Asset.objects.create(brief_description="Monitor", parent_asset=self.asset, current_location=self.stock)
        movement = transfer_asset(asset=self.asset, destination=lab, recipient=self.emp, approved_by=self.user, inventory_type="DIR")
        self.asset.refresh_from_db(); monitor.refresh_from_db()
        self.assertEqual((self.asset.inventory_type, self.asset.division), ("DIR", self.div))
        self.assertEqual((monitor.current_location, monitor.current_custodian), (lab, self.emp))
        changes = " | ".join(movement.changes)
        for expected in ("PIR/DIR: PIR", "Building: - \u2192 Main Block", "Room: 1 \u2192 9", "Name: - \u2192 Employee"):
            self.assertIn(expected, changes)

    def test_return_records_clause_and_division(self):
        transfer_asset(asset=self.asset, destination=self.office, recipient=self.emp, approved_by=self.user)
        movement = return_asset(asset=self.asset, stock_location=self.stock, returned_by=self.emp, approved_by=self.user, return_clause="Obsolete")
        self.assertEqual((movement.return_clause, movement.return_from_division, movement.returned_stock), ("Obsolete", self.div, True))
