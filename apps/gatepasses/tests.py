from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.assets.models import Asset
from .models import GatePass, GatePassItem
from .services import approve_gatepass, mark_outward, mark_inward
class GatePassTests(TestCase):
    def test_temporary_outward_and_inward(self):
        user = get_user_model().objects.create_user("security")
        asset = Asset.objects.create(asset_code="A1", transaction_id="T1", brief_description="Test")
        gp = GatePass.objects.create(gatepass_type=GatePass.Type.TEMPORARY, purpose="Repair", requested_by=user)
        GatePassItem.objects.create(gatepass=gp, asset=asset)
        approve_gatepass(gatepass=gp, user=user); mark_outward(gatepass=gp, user=user)
        asset.refresh_from_db(); self.assertEqual(asset.current_status, Asset.Status.OUTSIDE)
        mark_inward(gatepass=gp, user=user)
        gp.refresh_from_db(); asset.refresh_from_db(); self.assertEqual(gp.status, GatePass.Status.CLOSED); self.assertEqual(asset.current_status, Asset.Status.IN_STOCK)
