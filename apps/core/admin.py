from django import forms
from django.contrib import admin
from django.db import models
from .models import (
    Attachment, AuditEvent, Budget, BudgetClassification, Building, Centre, Division, Employee,
    Location, Place, ProjectCode, Room, Section, SubSection, Supplier,
)
from .widgets import AppDateInput


class StandardAdmin(admin.ModelAdmin):
    list_per_page = 50
    formfield_overrides = {models.DateField: {"widget": AppDateInput}}


admin.site.register([Division, Section, SubSection, Supplier, Attachment, Centre, Place, BudgetClassification, ProjectCode], StandardAdmin)


@admin.register(Building)
class BuildingAdmin(StandardAdmin):
    list_display = ("name", "centre", "is_active")
    list_filter = ("centre", "is_active")
    search_fields = ("name",)


@admin.register(Room)
class RoomAdmin(StandardAdmin):
    list_display = ("room_no", "building", "is_active")
    list_filter = ("building__centre", "building", "is_active")
    search_fields = ("room_no", "building__name")


@admin.register(Budget)
class BudgetAdmin(StandardAdmin):
    list_display = ("code", "name", "classification", "financial_year", "allocated_amount", "is_active")
    list_filter = ("classification", "financial_year", "is_active")
    search_fields = ("code", "name")


@admin.register(Employee)
class EmployeeAdmin(StandardAdmin):
    fields = ("employee_id", "name", "division", "section", "email", "date_of_joining", "date_of_retirement", "user", "is_active")
    list_display = ("employee_id", "name", "division", "date_of_joining", "date_of_retirement", "user", "is_active")
    list_filter = ("division", "is_active")
    search_fields = ("employee_id", "name", "email")


class LocationAdminForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("place", "building", "room", "division", "section", "sub_section", "is_stock_location", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["place"].required = True
        self.fields["place"].queryset = Place.objects.filter(is_active=True)
        self.fields["building"].queryset = Building.objects.filter(is_active=True).select_related("centre")
        self.fields["room"].queryset = Room.objects.filter(is_active=True).select_related("building")

    def clean(self):
        cleaned = super().clean()
        building, room = cleaned.get("building"), cleaned.get("room")
        if room and building and room.building_id != building.pk:
            self.add_error("room", "This room belongs to a different building.")
        if room and not building:
            cleaned["building"] = room.building
        return cleaned


@admin.register(Location)
class LocationAdmin(StandardAdmin):
    form = LocationAdminForm
    list_display = ("name", "building", "room_no", "division", "is_stock_location", "is_active")
    list_filter = ("building__centre", "building", "division", "is_stock_location", "is_active")
    search_fields = ("name", "room_no", "building__name")
    list_select_related = ("building", "division")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "description")
    list_filter = ("action", "object_type")
    search_fields = ("description", "object_id")
    readonly_fields = ("created_at",)
