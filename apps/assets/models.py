import uuid
from django.db import models
from apps.core.models import Employee, Location, Supplier, TimeStampedModel

class Asset(TimeStampedModel):
    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In stock"
        ASSIGNED = "ASSIGNED", "Assigned"
        OUTSIDE = "OUTSIDE", "Outside premises"
        RETURN_PENDING = "RETURN_PENDING", "Return pending"
        UNDER_DISPOSAL = "UNDER_DISPOSAL", "Under disposal"
        DISPOSED = "DISPOSED", "Disposed"
        WRITTEN_OFF = "WRITTEN_OFF", "Written off"
        PASSED_OUT = "PASSED_OUT", "Passed out"

    asset_code = models.CharField(max_length=50, unique=True)
    sl_no = models.PositiveIntegerField(null=True, blank=True, verbose_name="SL No.")
    transaction_id = models.CharField(max_length=100, unique=True)
    nc_no = models.CharField(max_length=100, blank=True, verbose_name="NC No.")
    nc_date = models.DateField(null=True, blank=True, verbose_name="NC date")
    brief_description = models.CharField(max_length=250)
    specification = models.TextField(blank=True)
    make = models.CharField(max_length=150, blank=True)
    model = models.CharField(max_length=150, blank=True)
    item_sl_no = models.CharField(max_length=150, blank=True, verbose_name="Item serial no.")
    current_status = models.CharField(max_length=30, choices=Status.choices, default=Status.IN_STOCK)
    current_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name="assets")
    current_custodian = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="assets")
    room_in_charge_name = models.CharField(max_length=150, blank=True)
    current_user = models.CharField(max_length=150, blank=True, help_text="Free-text legacy/current-user value")
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["asset_code"]
        permissions = [
            ("scan_asset", "Can scan asset QR pages"),
            ("view_sensitive_asset", "Can view sensitive asset details"),
        ]
    def __str__(self): return f"{self.asset_code} - {self.brief_description}"

class Procurement(TimeStampedModel):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="procurement")
    qty = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    po_no = models.CharField(max_length=100, blank=True)
    po_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT, related_name="procurements")
    bill_no = models.CharField(max_length=100, blank=True)
    bill_date = models.DateField(null=True, blank=True)
    bill_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    def __str__(self): return f"Procurement for {self.asset.asset_code}"

class Installation(TimeStampedModel):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="installation")
    stock_entry_reference = models.CharField(max_length=150, blank=True)
    date_of_installation = models.DateField(null=True, blank=True)
    warranty_period_months = models.PositiveIntegerField(null=True, blank=True)
    status_of_asset = models.CharField(max_length=100, blank=True)
    def __str__(self): return f"Installation for {self.asset.asset_code}"
