from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.assets.models import Asset
from .models import GatePass, GatePassItem
from .services import approve_gatepass, director_approve_gatepass, division_approve_gatepass, mark_outward, mark_inward, reject_gatepass
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
        user.is_superuser = True
        user.save()
        division_approve_gatepass(gatepass=gp, user=user)
        director_approve_gatepass(gatepass=gp, user=user)
        approve_gatepass(gatepass=gp, user=user)
        mark_outward(gatepass=gp, user=user)
        gp.refresh_from_db()
        asset.refresh_from_db()
        self.assertEqual(gp.status, GatePass.Status.OUTWARD)
        self.assertEqual(asset.current_status, Asset.Status.OUTSIDE)
        with self.assertRaisesMessage(ValidationError, "Only temporary gate passes"):
            mark_inward(gatepass=gp, user=user)

class GatePassApprovalFixtures:

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

    def make_gatepass(self, division=None, gatepass_type=GatePass.Type.TEMPORARY):
        gp = GatePass.objects.create(gatepass_type=gatepass_type, purpose="Test", requested_by=self.requester, division=division or self.div)
        GatePassItem.objects.create(gatepass=gp, asset=self.mine)
        return gp


class GatePassApprovalTests(GatePassApprovalFixtures, TestCase):
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


class GatePassCLRIWorkflowTests(GatePassApprovalFixtures, TestCase):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import Permission

        self.director = get_user_model().objects.create_user("director")
        self.director.user_permissions.add(Permission.objects.get(codename="director_approve_gatepass"))
        self.security = get_user_model().objects.create_user("gate-security")
        self.security.user_permissions.add(Permission.objects.get(codename="security_scan_gatepass"))
        for user in (self.div_admin, self.director, self.stores, self.security):
            user.user_permissions.add(Permission.objects.get(codename="view_gatepass"))

    def test_permanent_pass_requires_director_and_persists_attachment(self):
        from tempfile import TemporaryDirectory

        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from django.urls import reverse

        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.client.force_login(self.requester)
            response = self.client.post(reverse("gatepasses:create"), {
                "gatepass_type": GatePass.Type.PERMANENT,
                "assets": [self.mine.pk], "division": self.div.pk, "purpose": "Permanent removal",
                "attachment": SimpleUploadedFile("approval.txt", b"document"),
            })
            gp = GatePass.objects.get(purpose="Permanent removal")
            self.assertRedirects(response, reverse("gatepasses:detail", args=[gp.pk]))
            self.assertTrue(gp.attachment.name.endswith("/approval.txt"))
            download = self.client.get(reverse("gatepasses:attachment", args=[gp.pk]))
            self.assertEqual(b"".join(download.streaming_content), b"document")
            self.assertEqual(self.client.get(gp.attachment.url).status_code, 404)
            self.client.force_login(self.div_admin)
            self.client.post(reverse("gatepasses:division_approve", args=[gp.pk]))
            gp.refresh_from_db()
            self.assertEqual(gp.status, GatePass.Status.PENDING_DIRECTOR)
            self.client.force_login(self.stores)
            self.client.post(reverse("gatepasses:approve", args=[gp.pk]))
            gp.refresh_from_db()
            self.assertEqual(gp.status, GatePass.Status.PENDING_DIRECTOR)
            self.client.force_login(self.director)
            self.client.post(reverse("gatepasses:director_approve", args=[gp.pk]))
            gp.refresh_from_db()
            self.assertEqual(gp.director_approved_by, self.director)
            self.client.force_login(self.stores)
            self.client.post(reverse("gatepasses:approve", args=[gp.pk]))
            self.client.force_login(self.security)
            qr_url = reverse("assets:qr_page", args=[self.mine.qr_token])
            self.assertContains(self.client.get(qr_url), "Scan &amp; Mark Outward")
            self.client.post(reverse("gatepasses:outward", args=[gp.pk]))
            gp.refresh_from_db()
            self.assertEqual(gp.status, GatePass.Status.OUTWARD)
            self.assertNotContains(self.client.get(qr_url), "Mark Inward")

    def test_overdue_alerts_and_summary_cards(self):
        from datetime import timedelta

        from django.urls import reverse
        from django.utils import timezone

        overdue = GatePass.objects.create(
            gatepass_type=GatePass.Type.TEMPORARY, status=GatePass.Status.OUTWARD,
            expected_return_date=timezone.localdate() - timedelta(days=1), purpose="Overdue",
            requested_by=self.requester,
        )
        GatePass.objects.create(gatepass_type=GatePass.Type.PERMANENT, status=GatePass.Status.OUTWARD, purpose="Permanent")
        GatePass.objects.create(gatepass_type=GatePass.Type.TEMPORARY, status=GatePass.Status.CLOSED,
                                inward_at=timezone.now(), purpose="Returned")
        for user in (self.stores, self.security):
            self.client.force_login(user)
            for url in (reverse("core:dashboard"), reverse("gatepasses:list")):
                response = self.client.get(url)
                self.assertContains(response, "Overdue temporary gate passes")
                self.assertContains(response, overdue.gatepass_no)
                self.assertEqual(
                    tuple(response.context[name] for name in ("gp_returned", "gp_non_return", "gp_moved_out", "gp_moved_in")),
                    (1, 2, 2, 1),
                )
        self.client.force_login(self.requester)
        self.assertNotContains(self.client.get(reverse("core:dashboard")), "Overdue temporary gate passes")
