from django.conf import settings
from django.db import models
from apps.assets.models import Asset
from apps.core.models import TimeStampedModel

class DisposalRecord(TimeStampedModel):
    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        APPROVED = "APPROVED", "Approved"
        AUCTIONED = "AUCTIONED", "Auctioned"
        WRITTEN_OFF = "WRITTEN_OFF", "Written off"
        PASSED_OUT = "PASSED_OUT", "Passed out"

    asset = models.OneToOneField(Asset, on_delete=models.PROTECT, related_name="disposal_record")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PROPOSED)
    lot_name = models.CharField(max_length=150, blank=True, verbose_name="Disposal details / lot name")
    disposal_file_no = models.CharField(max_length=100, blank=True)
    auction_id = models.CharField(max_length=100, blank=True)
    h1_buyer = models.CharField(max_length=200, blank=True)
    emd_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    total_book_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    financial_year = models.CharField(max_length=20, blank=True)
    realized_sale_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    apportioned_sale_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    write_off_om_no = models.CharField(max_length=100, blank=True)
    write_off_om_date = models.DateField(null=True, blank=True)
    passout_for = models.CharField(max_length=150, blank=True)
    passout_type = models.CharField(max_length=100, blank=True)
    passout_no = models.CharField(max_length=100, blank=True)
    passout_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    remarks = models.TextField(blank=True)
    class Meta:
        ordering = ["-created_at"]
        permissions = [("approve_disposalrecord", "Can approve disposal and write-off")]
    def __str__(self): return f"Disposal {self.asset.asset_code}"
