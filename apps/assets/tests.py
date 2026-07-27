from django.test import TestCase
from .models import Asset
class AssetModelTests(TestCase):
    def test_asset_gets_unique_qr_token(self):
        a = Asset.objects.create(asset_code="A1", transaction_id="T1", brief_description="Test")
        self.assertIsNotNone(a.qr_token)
        self.assertEqual(str(a), "A1 - Test")
