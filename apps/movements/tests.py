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
