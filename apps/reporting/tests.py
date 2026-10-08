from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.assets.models import Asset
from apps.core.models import Division, Employee

class AssetReportTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", password="x"))
        div = Division.objects.create(code="CHEM", name="Chemistry")
        emp = Employee.objects.create(employee_id="E1", name="Asha", division=div)
        Asset.objects.create(brief_description="PIR item", inventory_type="PIR", current_custodian=emp)
        Asset.objects.create(brief_description="DIR item", inventory_type="DIR")

    def test_group_by_division_and_filter_by_inventory_type(self):
        response = self.client.get("/reports/assets/?group_by=division&inventory_type=PIR")
        self.assertEqual(response.context["groups"], [{"label": "Chemistry", "count": 1}])
        self.assertContains(response, "PIR item")
        self.assertNotContains(response, "DIR item")

    def test_employee_wise_and_date_filter(self):
        response = self.client.get("/reports/assets/?group_by=employee&date_from=01-01-2000&date_to=31-12-2999")
        self.assertIn({"label": "E1 / Asha", "count": 1}, response.context["groups"])
        self.assertEqual(self.client.get("/reports/assets/?date_to=01-01-2000").context["total"], 0)

    def test_csv_respects_filters(self):
        body = self.client.get("/reports/assets.csv?inventory_type=DIR").content.decode()
        self.assertIn("DIR item", body)
        self.assertNotIn("PIR item", body)
