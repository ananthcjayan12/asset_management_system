from django import forms
from apps.core.models import Location
from apps.core.widgets import AppDateInput, SearchableSelect
from .models import Asset, AssetVerification, Procurement, Installation

class YesNoSelect(forms.NullBooleanSelect):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.choices = (("unknown", "---------"), ("true", "Yes"), ("false", "No"))

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_code", "inventory_type", "nc_no", "nc_date", "brief_description", "specification", "make", "model", "item_sl_no", "parent_asset", "current_status", "current_location", "current_custodian", "division", "room_in_charge_name", "current_user", "remarks", "is_active"]
        widgets = {
            "nc_date": AppDateInput(), "specification": forms.Textarea(attrs={"rows": 3}), "remarks": forms.Textarea(attrs={"rows": 3}),
            "parent_asset": SearchableSelect(), "current_location": SearchableSelect(), "current_custodian": SearchableSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventory_type"].required = True
        self.fields["inventory_type"].choices = [("", "---------")] + list(Asset.InventoryType.choices)
        # Accessories hang off a main item; they are not main items themselves.
        main_items = Asset.objects.filter(is_active=True, parent_asset__isnull=True)
        if self.instance.pk:
            main_items = main_items.exclude(pk=self.instance.pk)
            if self.instance.accessories.exists():
                self.fields["parent_asset"].disabled = True
                self.fields["parent_asset"].help_text = "This item has accessories, so it cannot itself be an accessory."
        self.fields["parent_asset"].queryset = main_items
        self.fields["parent_asset"].required = False

class ProcurementForm(forms.ModelForm):
    class Meta:
        model = Procurement
        fields = ["qty", "currency", "amount", "po_no", "po_date", "supplier", "bill_no", "bill_date", "bill_value", "drr_no", "drr_date", "grin_no", "grin_date", "budget", "budget_classification", "project_code"]
        widgets = {"po_date": AppDateInput(), "bill_date": AppDateInput(), "drr_date": AppDateInput(), "grin_date": AppDateInput(), "supplier": SearchableSelect()}

class InstallationForm(forms.ModelForm):
    class Meta:
        model = Installation
        fields = ["stock_entry_reference", "date_of_installation", "warranty_period_months", "status_of_asset", "log_book_maintained"]
        widgets = {"date_of_installation": AppDateInput(), "log_book_maintained": YesNoSelect()}

class VerificationFilterForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.filter(is_active=True), required=False, widget=SearchableSelect(attrs={"class": "form-select"}))
    verification_date = forms.DateField(widget=AppDateInput())

class VerificationReportForm(forms.Form):
    date_from = forms.DateField(required=False, widget=AppDateInput(), label="From")
    date_to = forms.DateField(required=False, widget=AppDateInput(), label="To")
    result = forms.ChoiceField(required=False, choices=[("", "All results")] + list(AssetVerification.Result.choices), widget=forms.Select(attrs={"class": "form-select"}))
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, empty_label="All locations", widget=forms.Select(attrs={"class": "form-select"}))
