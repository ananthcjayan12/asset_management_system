from django import forms
from apps.assets.models import Asset
from apps.core.models import Building, Centre, Division, Employee, Location
from apps.core.widgets import AppDateInput, SearchableSelect

DATE_BASIS = {
    "registered": ("created_at__date", "Registration date"),
    "nc": ("nc_date", "NC date"),
    "bill": ("procurement__bill_date", "Bill date"),
    "installation": ("installation__date_of_installation", "Installation date"),
}

# key -> (fields to group on, heading)
GROUPINGS = {
    "employee": (["current_custodian__employee_id", "current_custodian__name"], "Employee name"),
    "division": (["division__name"], "Division"),
    "room": (["current_location__building__name", "current_location__room_no"], "Room"),
    "location": (["current_location__name"], "Location"),
    "building": (["current_location__building__name"], "Building"),
    "centre": (["current_location__building__centre__name"], "Centre"),
    "inventory_type": (["inventory_type"], "Type of inventory"),
    "status": (["current_status"], "Status"),
}

def select(**attrs):
    return forms.Select(attrs={"class": "form-select", **attrs})

class AssetReportForm(forms.Form):
    date_basis = forms.ChoiceField(choices=[(k, v[1]) for k, v in DATE_BASIS.items()], required=False, label="Date based on", widget=select())
    date_from = forms.DateField(required=False, widget=AppDateInput(), label="From")
    date_to = forms.DateField(required=False, widget=AppDateInput(), label="To")
    inventory_type = forms.ChoiceField(choices=[("", "PIR / DIR / IIR (all)")] + list(Asset.InventoryType.choices), required=False, label="Type of inventory", widget=select())
    status = forms.ChoiceField(choices=[("", "All statuses")] + list(Asset.Status.choices), required=False, widget=select())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False, label="Employee name", widget=SearchableSelect(attrs={"class": "form-select"}))
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, widget=select())
    centre = forms.ModelChoiceField(queryset=Centre.objects.all(), required=False, widget=select())
    building = forms.ModelChoiceField(queryset=Building.objects.select_related("centre"), required=False, widget=select())
    location = forms.ModelChoiceField(queryset=Location.objects.select_related("building"), required=False, label="Location / room", widget=SearchableSelect(attrs={"class": "form-select"}))
    group_by = forms.ChoiceField(choices=[("", "No grouping")] + [(k, v[1] + "-wise") for k, v in GROUPINGS.items()], required=False, label="Report", widget=select())

    def filter(self, qs):
        if not self.is_valid():
            return qs
        data = self.cleaned_data
        date_field = DATE_BASIS[data.get("date_basis") or "registered"][0]
        if data["date_from"]: qs = qs.filter(**{f"{date_field}__gte": data["date_from"]})
        if data["date_to"]: qs = qs.filter(**{f"{date_field}__lte": data["date_to"]})
        if data["inventory_type"]: qs = qs.filter(inventory_type=data["inventory_type"])
        if data["status"]: qs = qs.filter(current_status=data["status"])
        if data["employee"]: qs = qs.filter(current_custodian=data["employee"])
        if data["division"]: qs = qs.filter(division=data["division"])
        if data["centre"]: qs = qs.filter(current_location__building__centre=data["centre"])
        if data["building"]: qs = qs.filter(current_location__building=data["building"])
        if data["location"]: qs = qs.filter(current_location=data["location"])
        return qs
