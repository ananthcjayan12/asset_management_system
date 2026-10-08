from django.conf import settings
from django.db import models
from apps.assets.models import Asset
from apps.core.models import Division, Employee, Location, TimeStampedModel

class AssetMovement(TimeStampedModel):
    class ReturnClause(models.TextChoices):
        SURPLUS = "Surplus", "Surplus"
        OBSOLETE = "Obsolete", "Obsolete"
        UNSERVICEABLE = "Unserviceable", "Unserviceable"

    class Type(models.TextChoices):
        INITIAL_ASSIGNMENT = "INITIAL_ASSIGNMENT", "Initial assignment"
        TRANSFER = "TRANSFER", "Transfer"
        RETURN = "RETURN", "Return"
        GATE_OUT = "GATE_OUT", "Gate outward"
        GATE_IN = "GATE_IN", "Gate inward"
        DISPOSAL = "DISPOSAL", "Disposal"

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=30, choices=Type.choices)
    from_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_from")
    to_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_to")
    from_employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_from")
    to_employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_to")
    # Snapshot of what changed, so later edits to masters do not rewrite history.
    from_division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_from")
    to_division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_to")
    from_inventory_type = models.CharField(max_length=3, blank=True, verbose_name="From PIR/DIR")
    to_inventory_type = models.CharField(max_length=3, blank=True, verbose_name="To PIR/DIR")
    from_building = models.CharField(max_length=150, blank=True)
    to_building = models.CharField(max_length=150, blank=True)
    from_room = models.CharField(max_length=50, blank=True)
    to_room = models.CharField(max_length=50, blank=True)
    voucher_number = models.CharField(max_length=100, blank=True)
    movement_date = models.DateField(verbose_name="Transferred date")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_movements")
    remarks = models.TextField(blank=True)

    # Source-document transfer/return fields retained for reporting and migration.
    transfer = models.BooleanField(default=False)
    transfer_from_name = models.CharField(max_length=150, blank=True)
    transfer_from_id = models.CharField(max_length=50, blank=True)
    transfer_to_id = models.CharField(max_length=50, blank=True)
    transfer_to_name = models.CharField(max_length=150, blank=True)
    transfer_voucher_date = models.DateField(null=True, blank=True)
    returned_stock = models.BooleanField(default=False)
    return_from_name = models.CharField(max_length=150, blank=True)
    return_voucher_date = models.DateField(null=True, blank=True)
    return_clause = models.TextField(blank=True, choices=ReturnClause.choices)
    return_from_division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-movement_date", "-created_at"]
        permissions = [("approve_assetmovement", "Can approve and execute asset movements")]
    def __str__(self): return f"{self.asset.display_code} - {self.get_movement_type_display()}"

    @property
    def changes(self):
        """Human-readable list of what this movement changed."""
        rows = []
        def add(label, before, after):
            if (before or after) and before != after:
                rows.append(f"{label}: {before or '-'} \u2192 {after or '-'}")
        add("PIR/DIR", self.from_inventory_type, self.to_inventory_type)
        add("Division", getattr(self.from_division, "name", ""), getattr(self.to_division, "name", ""))
        if self.from_location_id != self.to_location_id and self.to_location_id:
            add("Location", getattr(self.from_location, "name", ""), getattr(self.to_location, "name", ""))
        add("Building", self.from_building, self.to_building)
        add("Room", self.from_room, self.to_room)
        if self.movement_type in {self.Type.TRANSFER, self.Type.RETURN}:
            add("Name", getattr(self.from_employee, "name", ""), getattr(self.to_employee, "name", ""))
        return rows
