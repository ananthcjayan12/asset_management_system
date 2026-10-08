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

class Centre(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name
    class Meta: ordering = ["name"]

class Building(TimeStampedModel):
    centre = models.ForeignKey(Centre, null=True, blank=True, on_delete=models.PROTECT, related_name="buildings")
    name = models.CharField(max_length=150, verbose_name="Building name")
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["centre__name", "name"]
        constraints = [models.UniqueConstraint(fields=["centre", "name"], name="unique_building_per_centre")]
    def __str__(self): return f"{self.name} ({self.centre})" if self.centre else self.name

class Room(TimeStampedModel):
    building = models.ForeignKey(Building, on_delete=models.PROTECT, related_name="rooms")
    room_no = models.CharField(max_length=50, verbose_name="Room No.")
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["building__name", "room_no"]
        constraints = [models.UniqueConstraint(fields=["building", "room_no"], name="unique_room_per_building")]
    def __str__(self): return f"{self.building.name} / {self.room_no}"

class Place(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True, verbose_name="Current place / location")
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name
    class Meta:
        ordering = ["name"]
        verbose_name = "current place / location"
        verbose_name_plural = "current places / locations"

class Location(TimeStampedModel):
    name = models.CharField(max_length=150, verbose_name="Current location")
    place = models.ForeignKey(Place, null=True, blank=True, on_delete=models.PROTECT, related_name="locations", verbose_name="Current location")
    building = models.ForeignKey(Building, null=True, blank=True, on_delete=models.PROTECT, related_name="locations", verbose_name="Building name")
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.PROTECT, related_name="locations", verbose_name="Room No.")
    room_no = models.CharField(max_length=50, blank=True)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    sub_section = models.ForeignKey(SubSection, null=True, blank=True, on_delete=models.PROTECT, related_name="locations")
    is_stock_location = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["name", "room_no"]
        constraints = [models.UniqueConstraint(fields=["name", "building", "room_no"], name="unique_named_building_room")]
    def save(self, *args, **kwargs):
        # The place/building/room drop-downs are the source of truth; the text
        # columns are kept in sync for imports, search and display.
        if self.place_id:
            self.name = self.place.name
        if self.room_id:
            self.room_no = self.room.room_no
            self.building_id = self.room.building_id
        super().save(*args, **kwargs)
    @property
    def centre(self): return self.building.centre if self.building_id else None
    def __str__(self):
        parts = [self.name, self.building.name if self.building_id else "", self.room_no]
        return " / ".join(p for p in parts if p)

class Employee(TimeStampedModel):
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    email = models.EmailField(blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_retirement = models.DateField(null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="employee", help_text="Login account of this employee; used to show only their own/division assets in gate passes.")
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

class BudgetClassification(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"
    class Meta: ordering = ["code"]

class Budget(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True, verbose_name="Budget code")
    name = models.CharField(max_length=200, verbose_name="Budget head")
    classification = models.ForeignKey(BudgetClassification, null=True, blank=True, on_delete=models.PROTECT, related_name="budgets")
    financial_year = models.CharField(max_length=20, blank=True)
    allocated_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"
    class Meta:
        ordering = ["code"]
        verbose_name = "budget master"
        verbose_name_plural = "budget master"

class ProjectCode(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"
    class Meta: ordering = ["code"]

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
