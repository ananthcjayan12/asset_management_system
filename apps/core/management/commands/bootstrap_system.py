import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.assets.models import Asset, Installation, Procurement
from apps.core.models import Division, Employee, Location, Section, Supplier
from apps.core.roles import ensure_groups

class Command(BaseCommand):
    help = "Create roles, initial administrator, reference data and optional demo assets."
    def add_arguments(self, parser):
        parser.add_argument("--no-demo", action="store_true")
    def handle(self, *args, **opts):
        ensure_groups()
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
            asset, made = Asset.objects.get_or_create(asset_code="AST-DEMO-001", defaults={"transaction_id": "TX-DEMO-001", "inventory_type": Asset.InventoryType.PIR, "brief_description": "Demo laptop", "make": "Example", "model": "Model 1", "item_sl_no": "SN-DEMO-001", "current_status": Asset.Status.ASSIGNED, "current_location": office, "current_custodian": emp})
            if made:
                Procurement.objects.create(asset=asset, qty=1, amount=50000, po_no="PO-DEMO-001", supplier=supplier)
                Installation.objects.create(asset=asset, stock_entry_reference="SE-DEMO-001", status_of_asset="Working")
        self.stdout.write(self.style.SUCCESS("Bootstrap completed."))
