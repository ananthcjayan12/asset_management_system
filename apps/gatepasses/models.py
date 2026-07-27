import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.models import Division, TimeStampedModel

class GatePass(TimeStampedModel):
    class Type(models.TextChoices):
        TEMPORARY = "TEMPORARY", "Temporary"
        PERMANENT = "PERMANENT", "Permanent"
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        STORES_APPROVED = "STORES_APPROVED", "Stores approved"
        REJECTED = "REJECTED", "Rejected"
        OUTWARD = "OUTWARD", "Marked outward"
        INWARD = "INWARD", "Marked inward"
        CLOSED = "CLOSED", "Closed"

    gatepass_no = models.CharField(max_length=50, unique=True, blank=True)
    gatepass_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.REQUESTED)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="gatepasses")
    purpose = models.TextField()
    destination = models.CharField(max_length=250, blank=True)
    expected_return_date = models.DateField(null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="requested_gatepasses")
    stores_marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="stores_gatepasses")
    security_out_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="security_out_gatepasses")
    security_in_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="security_in_gatepasses")
    outward_at = models.DateTimeField(null=True, blank=True)
    inward_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("approve_gatepass", "Can approve gate passes in stores"),
            ("security_scan_gatepass", "Can mark gate pass outward and inward"),
        ]
    def save(self, *args, **kwargs):
        if not self.gatepass_no:
            self.gatepass_no = f"GP-{timezone.localdate():%Y%m}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    def __str__(self): return self.gatepass_no or "New gate pass"

class GatePassItem(TimeStampedModel):
    gatepass = models.ForeignKey(GatePass, on_delete=models.CASCADE, related_name="items")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="gatepass_items")
    outward_scanned = models.BooleanField(default=False)
    inward_scanned = models.BooleanField(default=False)
    remarks = models.CharField(max_length=250, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["gatepass", "asset"], name="unique_asset_per_gatepass")]
    def __str__(self): return f"{self.gatepass} / {self.asset.asset_code}"
