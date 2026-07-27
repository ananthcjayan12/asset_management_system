from django.conf import settings
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Division(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150, unique=True)
    def __str__(self): return f"{self.code} - {self.name}"
    class Meta: ordering = ["name"]

class Section(TimeStampedModel):
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="sections")
    name = models.CharField(max_length=150)
    class Meta:
        ordering = ["division__name", "name"]
        constraints = [models.UniqueConstraint(fields=["division", "name"], name="unique_section_per_division")]
    def __str__(self): return f"{self.division.code} / {self.name}"

class SubSection(TimeStampedModel):
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="subsections")
    name = models.CharField(max_length=150)
    class Meta:
        ordering = ["section__division__name", "section__name", "name"]
        constraints = [models.UniqueConstraint(fields=["section", "name"], name="unique_subsection_per_section")]
    def __str__(self): return f"{self.section} / {self.name}"

class Location(TimeStampedModel):
    name = models.CharField(max_length=150)
    room_no = models.CharField(max_length=50, blank=True)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    sub_section = models.ForeignKey(SubSection, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    is_stock_location = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["name", "room_no"]
        constraints = [models.UniqueConstraint(fields=["name", "room_no"], name="unique_named_room")]
    def __str__(self): return f"{self.name}{' / ' + self.room_no if self.room_no else ''}"

class Employee(TimeStampedModel):
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.employee_id} - {self.name}"
    class Meta: ordering = ["name"]

class Supplier(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    def __str__(self): return self.name
    class Meta: ordering = ["name"]

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.action}: {self.description[:60]}"

class Attachment(TimeStampedModel):
    asset = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to="asset_attachments/%Y/%m/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self): return self.title
