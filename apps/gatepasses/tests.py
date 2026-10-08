from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.assets.models import Asset
from .models import GatePass, GatePassItem
from .services import approve_gatepass, division_approve_gatepass, mark_outward, mark_inward, reject_gatepass
class GatePassTests(TestCase):
    def test_temporary_outward_and_inward(self):
        user = get_user_model().objects.create_user("security")
        asset = Asset.objects.create(asset_code="A1", transaction_id="T1", brief_description="Test")
        gp = GatePass.objects.create(gatepass_type=GatePass.Type.TEMPORARY, purpose="Repair", requested_by=user)
        GatePassItem.objects.create(gatepass=gp, asset=asset)
        user.is_superuser = True; user.save()
        division_approve_gatepass(gatepass=gp, user=user); approve_gatepass(gatepass=gp, user=user); mark_outward(gatepass=gp, user=user)
        asset.refresh_from_db(); self.assertEqual(asset.current_status, Asset.Status.OUTSIDE)
        mark_inward(gatepass=gp, user=user)
        gp.refresh_from_db(); asset.refresh_from_db(); self.assertEqual(gp.status, GatePass.Status.CLOSED); self.assertEqual(asset.current_status, Asset.Status.IN_STOCK)

    def test_permanent_gatepass_remains_outward_without_inward_action(self):
        user = get_user_model().objects.create_user("permanent-security")
        asset = Asset.objects.create(asset_code="A2", transaction_id="T2", brief_description="Permanent pass asset")
        gp = GatePass.objects.create(gatepass_type=GatePass.Type.PERMANENT, purpose="Permanent removal", requested_by=user)
        GatePassItem.objects.create(gatepass=gp, asset=asset)
        division_approve_gatepass(gatepass=gp, user=user)
        approve_gatepass(gatepass=gp, user=user)
        mark_outward(gatepass=gp, user=user)
        gp.refresh_from_db()
        asset.refresh_from_db()
        self.assertEqual(gp.status, GatePass.Status.OUTWARD)
        self.assertEqual(asset.current_status, Asset.Status.OUTSIDE)
        with self.assertRaisesMessage(ValidationError, "Only temporary gate passes"):
            mark_inward(gatepass=gp, user=user)

class GatePassApprovalTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Permission
        from apps.core.models import Division, Employee
        self.div = Division.objects.create(code="D1", name="Division One")
        self.other = Division.objects.create(code="D2", name="Division Two")
        User = get_user_model()
        self.requester = User.objects.create_user("requester")
        self.requester_emp = Employee.objects.create(employee_id="E1", name="Requester", division=self.div, user=self.requester)
        self.div_admin = User.objects.create_user("divadmin")
        self.div_admin.user_permissions.add(Permission.objects.get(codename="division_approve_gatepass"))
        Employee.objects.create(employee_id="E2", name="Division Admin", division=self.div, user=self.div_admin)
        self.stores = User.objects.create_user("stores")
        self.stores.user_permissions.add(Permission.objects.get(codename="approve_gatepass"))
        self.mine = Asset.objects.create(brief_description="Mine", current_custodian=self.requester_emp)
        self.division_item = Asset.objects.create(brief_description="Division item", division=self.div)
        self.other_item = Asset.objects.create(brief_description="Other division", division=self.other)

    def make_gatepass(self, division=None):
        gp = GatePass.objects.create(gatepass_type=GatePass.Type.PERMANENT, purpose="Test", requested_by=self.requester, division=division or self.div)
        GatePassItem.objects.create(gatepass=gp, asset=self.mine)
        return gp

    def test_requester_sees_only_own_and_division_items(self):
        from .forms import GatePassForm
        form = GatePassForm(user=self.requester)
        self.assertEqual(set(form.fields["assets"].queryset), {self.mine, self.division_item})

    def test_stores_cannot_approve_before_division(self):
        gp = self.make_gatepass()
        with self.assertRaisesMessage(ValidationError, "division admin must approve"):
            approve_gatepass(gatepass=gp, user=self.stores)
        division_approve_gatepass(gatepass=gp, user=self.div_admin)
        approve_gatepass(gatepass=gp, user=self.stores)
        gp.refresh_from_db()
        self.assertEqual(gp.status, GatePass.Status.STORES_APPROVED)

    def test_division_admin_limited_to_own_division(self):
        gp = self.make_gatepass(division=self.other)
        with self.assertRaisesMessage(ValidationError, "own division"):
            division_approve_gatepass(gatepass=gp, user=self.div_admin)

    def test_division_admin_and_stores_can_reject(self):
        gp = self.make_gatepass()
        reject_gatepass(gatepass=gp, user=self.div_admin, reason="Not needed")
        gp.refresh_from_db()
        self.assertEqual((gp.status, gp.rejection_reason, gp.rejected_by), (GatePass.Status.REJECTED, "Not needed", self.div_admin))
        gp2 = self.make_gatepass()
        division_approve_gatepass(gatepass=gp2, user=self.div_admin)
        reject_gatepass(gatepass=gp2, user=self.stores, reason="Item required on site")
        gp2.refresh_from_db()
        self.assertEqual(gp2.status, GatePass.Status.REJECTED)

    def test_security_scan_is_not_granted_to_system_administrator_group(self):
        from django.contrib.auth.models import Group
        from apps.core.roles import ensure_groups
        ensure_groups()
        self.assertFalse(Group.objects.get(name="System Administrator").permissions.filter(codename="security_scan_gatepass").exists())
        self.assertTrue(Group.objects.get(name="Security Officer").permissions.filter(codename="security_scan_gatepass").exists())
