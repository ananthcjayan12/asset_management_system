from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assets.models import Asset
from apps.core.demo_data import (
    ADMIN_USERNAME,
    VIEWER_USERNAME,
    cleanup_demo_data,
    prepare_demo_data,
)
from apps.core.models import Division, Location


class PlaywrightDemoDataTests(TestCase):
    def test_prepare_is_idempotent_and_cleanup_is_prefix_scoped(self):
        ordinary = Asset.objects.create(
            asset_code="ORDINARY-001",
            transaction_id="ORDINARY-TX-001",
            brief_description="Ordinary record that cleanup must retain",
        )

        first = prepare_demo_data()
        second = prepare_demo_data()

        self.assertEqual(first["assets"], second["assets"])
        self.assertEqual(Asset.objects.filter(asset_code__startswith="PWDEMO").count(), 4)
        self.assertTrue(get_user_model().objects.filter(username=ADMIN_USERNAME, is_superuser=True).exists())
        self.assertTrue(get_user_model().objects.filter(username=VIEWER_USERNAME, groups__name="Report Viewer").exists())
        self.assertTrue(Location.objects.filter(name="PW Demo Central Stores", is_stock_location=True).exists())

        counts = cleanup_demo_data()

        self.assertEqual(counts["assets"], 4)
        self.assertFalse(Asset.objects.filter(asset_code__startswith="PWDEMO").exists())
        self.assertFalse(get_user_model().objects.filter(username__in=[ADMIN_USERNAME, VIEWER_USERNAME]).exists())
        self.assertFalse(Division.objects.filter(code="PWDEMO").exists())
        self.assertTrue(Asset.objects.filter(pk=ordinary.pk).exists())

    def test_report_viewer_navigation_hides_unpermitted_actions(self):
        prepare_demo_data()
        self.assertTrue(self.client.login(username=VIEWER_USERNAME, password="PlaywrightViewer123!"))

        dashboard = self.client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Assets")
        self.assertContains(dashboard, "Movements")
        self.assertContains(dashboard, "Disposal")
        self.assertNotContains(dashboard, "Administration")
        self.assertNotContains(dashboard, ">Import<")

        gatepasses = self.client.get("/gatepasses/")
        self.assertEqual(gatepasses.status_code, 200)
        self.assertNotContains(gatepasses, "Request gate pass")
