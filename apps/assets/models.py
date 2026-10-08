import uuid
from django.conf import settings
from django.db import models
from django.db.models import Max
from django.utils import timezone
from apps.core.models import Budget, BudgetClassification, Division, Employee, Location, ProjectCode, Supplier, TimeStampedModel

class Asset(TimeStampedModel):
    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In stock"
        ASSIGNED = "ASSIGNED", "Issued"
        OUTSIDE = "OUTSIDE", "Outside premises"
        RETURN_PENDING = "RETURN_PENDING", "Return pending"
        UNDER_DISPOSAL = "UNDER_DISPOSAL", "Under disposal"
        DISPOSED = "DISPOSED", "Disposed"
        WRITTEN_OFF = "WRITTEN_OFF", "Written Off"
        PASSED_OUT = "PASSED_OUT", "Passed Out"

    class InventoryType(models.TextChoices):
        PIR = "PIR", "PIR"
        DIR = "DIR", "DIR"
        IIR = "IIR", "IIR"

    asset_code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="RFID code", help_text="Optional. Can be added later when the RFID tag is fixed.")
    inventory_type = models.CharField(max_length=3, choices=InventoryType.choices, blank=True, verbose_name="Type of inventory")
    sl_no = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name="SL No.")
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    nc_no = models.CharField(max_length=100, blank=True, verbose_name="NC No.")
    nc_date = models.DateField(null=True, blank=True, verbose_name="NC date")
    brief_description = models.CharField(max_length=250)
    specification = models.TextField(blank=True)
    make = models.CharField(max_length=150, blank=True)
    model = models.CharField(max_length=150, blank=True)
    item_sl_no = models.CharField(max_length=150, blank=True, verbose_name="Item serial no.")
    parent_asset = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="accessories", verbose_name="Main item", help_text="For accessories (monitor, keyboard, etc.), choose the main item they belong to.")
    current_status = models.CharField(max_length=30, choices=Status.choices, default=Status.IN_STOCK)
    current_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name="assets")
    current_custodian = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.PROTECT, related_name="assets")
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="assets", help_text="Leave blank to use the custodian's or location's division.")
    room_in_charge_name = models.CharField(max_length=150, blank=True)
    current_user = models.CharField(max_length=150, blank=True, help_text="Free-text legacy/current-user value")
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sl_no", "id"]
        permissions = [
            ("scan_asset", "Can scan asset QR pages"),
            ("view_sensitive_asset", "Can view sensitive asset details"),
        ]

    @staticmethod
    def next_transaction_id(on_date=None):
        """dd-mm-yyyy followed by a running number for that day, e.g. 07-10-2026-0003."""
        prefix = f"{(on_date or timezone.localdate()):%d-%m-%Y}-"
        numbers = [int(tx[len(prefix):]) for tx in Asset.objects.filter(transaction_id__startswith=prefix).values_list("transaction_id", flat=True) if tx[len(prefix):].isdigit()]
        return f"{prefix}{max(numbers, default=0) + 1:04d}"

    def save(self, *args, **kwargs):
        if not self.asset_code:
            self.asset_code = None
        if self.sl_no is None:
            self.sl_no = (Asset.objects.aggregate(m=Max("sl_no"))["m"] or 0) + 1
        if not self.transaction_id:
            self.transaction_id = self.next_transaction_id()
        if self.division_id is None:
            self.division = getattr(self.current_custodian, "division", None) or getattr(self.current_location, "division", None)
        super().save(*args, **kwargs)

    @property
    def display_code(self): return self.asset_code or self.transaction_id
    def __str__(self): return f"{self.display_code} - {self.brief_description}"

class Procurement(TimeStampedModel):
    class Currency(models.TextChoices):
        INR = "INR", "Rupee (₹)"
        USD = "USD", "US Dollar ($)"
        EUR = "EUR", "Euro (€)"
        JPY = "JPY", "Yen (¥)"

    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="procurement")
    qty = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.INR, help_text="Currency of the unit rate and bill value.")
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Amount / Unit rate")
    po_no = models.CharField(max_length=100, blank=True, verbose_name="PO No.")
    po_date = models.DateField(null=True, blank=True, verbose_name="PO date")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT, related_name="procurements")
    bill_no = models.CharField(max_length=100, blank=True, verbose_name="Bill No.")
    bill_date = models.DateField(null=True, blank=True)
    bill_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    drr_no = models.CharField(max_length=100, blank=True, verbose_name="DRR No.")
    drr_date = models.DateField(null=True, blank=True, verbose_name="DRR date")
    grin_no = models.CharField(max_length=100, blank=True, verbose_name="GRIN No.")
    grin_date = models.DateField(null=True, blank=True, verbose_name="GRIN date")
    budget = models.ForeignKey(Budget, null=True, blank=True, on_delete=models.PROTECT, related_name="procurements")
    budget_classification = models.ForeignKey(BudgetClassification, null=True, blank=True, on_delete=models.PROTECT, related_name="procurements")
    project_code = models.ForeignKey(ProjectCode, null=True, blank=True, on_delete=models.PROTECT, related_name="procurements")
    def __str__(self): return f"Procurement for {self.asset.display_code}"

class Installation(TimeStampedModel):
    class WorkingStatus(models.TextChoices):
        WORKING = "Working", "Working"
        NOT_WORKING = "Not working", "Not working"

    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="installation")
    stock_entry_reference = models.CharField(max_length=150, blank=True)
    date_of_installation = models.DateField(null=True, blank=True)
    warranty_period_months = models.PositiveIntegerField(null=True, blank=True)
    status_of_asset = models.CharField(max_length=100, blank=True, choices=WorkingStatus.choices)
    log_book_maintained = models.BooleanField(null=True, blank=True, verbose_name="Log book maintained")
    def __str__(self): return f"Installation for {self.asset.display_code}"

class AssetVerification(TimeStampedModel):
    class Result(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        NOT_AVAILABLE = "NOT_AVAILABLE", "Not available"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="verifications")
    verification_date = models.DateField(default=timezone.localdate)
    result = models.CharField(max_length=20, choices=Result.choices)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, related_name="verifications", help_text="Where the asset was expected during verification.")
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    remarks = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["-verification_date", "-created_at"]
    def __str__(self): return f"{self.asset.display_code} - {self.get_result_display()} ({self.verification_date})"
