from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from apps.assets.models import Asset
from apps.core.models import Location
from apps.core.roles import ensure_groups
from apps.movements.services import return_asset

class DisposalTests(TestCase):
    def setUp(self):
        ensure_groups()
        User = get_user_model()
        self.stores = User.objects.create_user("stores", password="x"); self.stores.groups.add(Group.objects.get(name="Stores Officer"))
        self.asset_admin = User.objects.create_user("assetadmin", password="x"); self.asset_admin.groups.add(Group.objects.get(name="Asset Administrator"))
        stock = Location.objects.create(name="Stores", room_no="S1", is_stock_location=True)
        self.asset = Asset.objects.create(brief_description="Old printer")
        return_asset(asset=self.asset, stock_location=stock, returned_by=None, approved_by=self.stores, return_clause="Unserviceable")

    def test_lot_classification_is_stores_only(self):
        self.client.force_login(self.asset_admin)
        response = self.client.get("/disposal/new/")
        self.assertTrue(response.context["form"].fields["lot_name"].disabled)
        self.assertContains(response, ">Save<")
        self.client.force_login(self.stores)
        self.assertFalse(self.client.get("/disposal/new/").context["form"].fields["lot_name"].disabled)

    def test_stores_returns_tab_lists_return_clause(self):
        self.client.force_login(self.stores)
        response = self.client.get("/disposal/?tab=returns&clause=Unserviceable")
        self.assertContains(response, "Old printer")
        self.assertContains(response, "Classify into lot")
        self.assertNotContains(self.client.get("/disposal/?tab=returns&clause=Surplus"), "Old printer")
