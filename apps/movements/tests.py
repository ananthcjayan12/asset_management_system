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


class MovementWorkflowTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group

        from apps.core.roles import ensure_groups

        ensure_groups()
        self.division = Division.objects.create(code="SEND", name="Sending Division")
        self.receiving = Division.objects.create(code="RECV", name="Receiving Division")
        self.staff = self.employee("initiator", self.division)
        self.recipient = self.employee("recipient", self.division)
        self.other_recipient = self.employee("other-recipient", self.receiving)
        self.hod = self.employee("sending-hod", self.division)
        self.receiving_hod = self.employee("receiving-hod", self.receiving)
        for hod in (self.hod, self.receiving_hod):
            hod.groups.add(Group.objects.get(name="Division Administrator"))
        self.ca = get_user_model().objects.create_user("ca")
        self.stores = get_user_model().objects.create_user("stores")
        self.da = get_user_model().objects.create_user("da")
        for user, role in ((self.ca, "Approving Officer"), (self.stores, "Stores Officer"), (self.da, "Asset Administrator")):
            user.groups.add(Group.objects.get(name=role))
        self.stock = Location.objects.create(name="Central Stores", is_stock_location=True)

    def employee(self, username, division):
        user = get_user_model().objects.create_user(username)
        Employee.objects.create(user=user, employee_id=username, name=username, division=division)
        return user

    def asset(self):
        return Asset.objects.create(brief_description="Staff equipment", current_custodian=self.staff.employee,
                                    current_status=Asset.Status.ASSIGNED, nc_no="NC-445")

    def action(self, user, movement, expected, **data):
        from django.urls import reverse

        self.client.force_login(user)
        response = self.client.post(reverse("movements:action", args=[movement.pk]), {
            "status": movement.workflow_status, **data,
        })
        self.assertRedirects(response, reverse("movements:list"))
        movement.refresh_from_db()
        self.assertEqual(movement.workflow_status, expected)

    def test_store_return_approval_chain_and_scoped_returns_tab(self):
        from django.urls import reverse
        from django.utils import timezone

        from apps.disposal.models import DisposalRecord
        from .models import AssetMovement

        status = AssetMovement.WorkflowStatus
        asset = self.asset()
        self.client.force_login(self.staff)
        response = self.client.post(reverse("movements:return"), {
            "asset": asset.pk, "movement_date": timezone.localdate().isoformat(),
            "material_category": "Furniture", "return_nature": "RETURNABLE", "return_clause": "Surplus",
        })
        self.assertRedirects(response, reverse("movements:list"))
        movement = asset.movements.get()
        self.assertEqual(movement.workflow_status, status.PENDING_HOD)
        asset.refresh_from_db()
        self.assertEqual(asset.current_status, Asset.Status.RETURN_PENDING)
        self.assertContains(self.client.get("/disposal/?tab=returns"), "Staff equipment")
        self.client.force_login(self.recipient)
        self.assertNotContains(self.client.get("/disposal/?tab=returns"), "Staff equipment")

        self.action(self.hod, movement, status.PENDING_CA)
        self.action(self.ca, movement, status.PENDING_SO, material_category="E-Waste",
                    return_nature="NON_RETURNABLE", return_clause="Obsolete")
        self.action(self.stores, movement, status.PENDING_DA, material_category="Machinery",
                    return_nature="NON_RETURNABLE", return_clause="Unserviceable")
        self.action(self.da, movement, status.COMPLETED, lot_name="Auction lot 1")
        asset.refresh_from_db()
        self.assertEqual(asset.current_status, Asset.Status.IN_STOCK)
        self.assertEqual(asset.current_location, self.stock)
        self.assertIsNone(asset.current_custodian)
        self.assertEqual(DisposalRecord.objects.get(asset=asset).lot_name, "Auction lot 1")

        self.client.force_login(self.staff)
        response = self.client.get("/disposal/", {"tab": "returns", "clause": "Unserviceable", "category": "Machinery"})
        for text in ("NC-445", "Completed", "Non-returnable", "Auction lot 1"):
            self.assertContains(response, text)
        self.assertContains(self.client.get("/"), "Your completed Stores returns")

    def test_transfer_requires_receiving_hod_only_across_divisions(self):
        from django.urls import reverse
        from django.utils import timezone

        from .models import AssetMovement

        status = AssetMovement.WorkflowStatus
        for recipient, cross_division in ((self.recipient, False), (self.other_recipient, True)):
            with self.subTest(cross_division=cross_division):
                asset = self.asset()
                destination = Location.objects.create(name="Destination", division=recipient.employee.division)
                accessory = Asset.objects.create(brief_description="Accessory", parent_asset=asset)
                self.client.force_login(self.staff)
                response = self.client.post(reverse("movements:transfer"), {
                    "asset": asset.pk, "destination": destination.pk, "recipient": recipient.employee.pk,
                    "movement_date": timezone.localdate().isoformat(), "include_accessories": "on",
                })
                self.assertRedirects(response, reverse("movements:list"))
                movement = asset.movements.get()
                self.action(self.hod, movement, status.PENDING_RECIPIENT)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(reverse("movements:action", args=[movement.pk])).status_code, 403)
                next_status = status.PENDING_RECEIVING_HOD if cross_division else status.PENDING_SO
                self.action(recipient, movement, next_status)
                if cross_division:
                    self.action(self.receiving_hod, movement, status.PENDING_SO)
                self.action(self.stores, movement, status.PENDING_DA)
                asset.refresh_from_db()
                self.assertEqual(asset.current_custodian, self.staff.employee)
                self.action(self.da, movement, status.COMPLETED)
                asset.refresh_from_db()
                accessory.refresh_from_db()
                self.assertEqual((asset.current_custodian, asset.division, asset.current_location),
                                 (recipient.employee, recipient.employee.division, destination))
                self.assertEqual(accessory.current_custodian, recipient.employee)
