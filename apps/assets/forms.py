from django import forms
from .models import Asset, Procurement, Installation

class DateInput(forms.DateInput): input_type = "date"

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_code", "sl_no", "transaction_id", "nc_no", "nc_date", "brief_description", "specification", "make", "model", "item_sl_no", "current_status", "current_location", "current_custodian", "room_in_charge_name", "current_user", "remarks", "is_active"]
        widgets = {"nc_date": DateInput(), "specification": forms.Textarea(attrs={"rows": 3}), "remarks": forms.Textarea(attrs={"rows": 3})}

class ProcurementForm(forms.ModelForm):
    class Meta:
        model = Procurement
        exclude = ["asset"]
        widgets = {"po_date": DateInput(), "bill_date": DateInput()}

class InstallationForm(forms.ModelForm):
    class Meta:
        model = Installation
        exclude = ["asset"]
        widgets = {"date_of_installation": DateInput()}
