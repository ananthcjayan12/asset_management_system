from django.conf import settings
from django.db import models
from apps.assets.models import Asset
from apps.core.models import TimeStampedModel

class ImportBatch(TimeStampedModel):
    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        VALIDATED = "VALIDATED", "Validated"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
    uploaded_file = models.FileField(upload_to="imports/%Y/%m/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"Import #{self.pk} ({self.get_status_display()})"

class ImportRow(TimeStampedModel):
    class ValidationStatus(models.TextChoices):
        VALID = "VALID", "Valid"
        INVALID = "INVALID", "Invalid"
        IMPORTED = "IMPORTED", "Imported"
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="rows")
    row_number = models.PositiveIntegerField()
    original_data = models.JSONField(default=dict)
    validation_status = models.CharField(max_length=20, choices=ValidationStatus.choices)
    validation_errors = models.JSONField(default=list, blank=True)
    created_asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ["row_number"]
        constraints = [models.UniqueConstraint(fields=["batch", "row_number"], name="unique_import_row")]
    def __str__(self): return f"Batch {self.batch_id}, row {self.row_number}"
