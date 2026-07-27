import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from apps.assets.models import Asset, Installation, Procurement
from apps.core.models import Division, Employee, Location, Section, Supplier

GROUP_PERMISSIONS = {
    "System Administrator": ["add", "change", "delete", "view"],
    "Asset Administrator": ["add_asset", "change_asset", "view_asset", "add_procurement", "change_procurement", "view_procurement", "add_installation", "change_installation", "view_installation", "approve_assetmovement", "view_assetmovement", "add_disposalrecord", "change_disposalrecord", "view_disposalrecord", "add_importbatch", "change_importbatch", "view_importbatch"],
    "Stores Officer": ["view_asset", "change_asset", "approve_assetmovement", "view_assetmovement", "approve_gatepass", "view_gatepass", "change_gatepass"],
    "Division Officer": ["view_asset", "add_gatepass", "view_gatepass", "view_assetmovement"],
    "Approving Officer": ["view_asset", "approve_assetmovement", "approve_disposalrecord", "change_disposalrecord", "view_disposalrecord"],
    "Security Officer": ["view_asset", "scan_asset", "view_gatepass", "security_scan_gatepass", "change_gatepass"],
    "Auditor": ["view_asset", "view_procurement", "view_installation", "view_assetmovement", "view_gatepass", "view_disposalrecord", "view_auditevent"],
    "Report Viewer": ["view_asset", "view_gatepass", "view_assetmovement", "view_disposalrecord"],
}

class Command(BaseCommand):
    help = "Create roles, initial administrator, reference data and optional demo assets."
    def add_arguments(self, parser):
        parser.add_argument("--no-demo", action="store_true")
    def handle(self, *args, **opts):
        for name, codenames in GROUP_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=name)
            if name == "System Administrator":
                group.permissions.set(Permission.objects.all())
            else:
                group.permissions.set(Permission.objects.filter(codename__in=codenames))
        User = get_user_model()
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "ChangeMe123!")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.local")
        user, created = User.objects.get_or_create(username=username, defaults={"email": email, "is_staff": True, "is_superuser": True})
        if created or os.getenv("RESET_ADMIN_PASSWORD", "False").lower() == "true":
            user.set_password(password); user.save()
        if not opts["no_demo"]:
            div, _ = Division.objects.get_or_create(code="ITD", defaults={"name": "Information Technology Division"})
            section, _ = Section.objects.get_or_create(division=div, name="Infrastructure")
            stock, _ = Location.objects.get_or_create(name="Central Stores", room_no="ST-01", defaults={"division": div, "section": section, "is_stock_location": True})
            office, _ = Location.objects.get_or_create(name="IT Office", room_no="204", defaults={"division": div, "section": section})
            emp, _ = Employee.objects.get_or_create(employee_id="EMP001", defaults={"name": "Demo Custodian", "division": div, "section": section})
            supplier, _ = Supplier.objects.get_or_create(name="Demo Supplier")
            asset, made = Asset.objects.get_or_create(asset_code="AST-DEMO-001", defaults={"transaction_id": "TX-DEMO-001", "brief_description": "Demo laptop", "make": "Example", "model": "Model 1", "item_sl_no": "SN-DEMO-001", "current_status": Asset.Status.ASSIGNED, "current_location": office, "current_custodian": emp})
            if made:
                Procurement.objects.create(asset=asset, qty=1, amount=50000, po_no="PO-DEMO-001", supplier=supplier)
                Installation.objects.create(asset=asset, stock_entry_reference="SE-DEMO-001", status_of_asset="Working")
        self.stdout.write(self.style.SUCCESS("Bootstrap completed."))
