from django import forms
from django.urls import reverse_lazy
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.models import Division, Employee, Location
from apps.core.widgets import AppDateInput, SearchableSelect
from .models import AssetMovement

def asset_picker():
    """Searchable asset drop-down that loads the asset's details when chosen."""
    return SearchableSelect(attrs={"hx-get": reverse_lazy("assets:summary"), "hx-trigger": "change, load", "hx-target": "#asset-summary"})

class TransferForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True), widget=asset_picker())
    include_accessories = forms.BooleanField(required=False, initial=True, label="Also transfer the accessories attached to this item")
    destination = forms.ModelChoiceField(queryset=Location.objects.filter(is_active=True), widget=SearchableSelect(), help_text="Choose the new place / building / room.")
    recipient = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False, widget=SearchableSelect(), label="Transfer to (name)")
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, label="New division", help_text="Leave blank to take the recipient's or destination's division.")
    inventory_type = forms.ChoiceField(choices=[("", "Keep current")] + list(Asset.InventoryType.choices), required=False, label="Change PIR/DIR")
    voucher_number = forms.CharField(max_length=100, required=False, label="Transfer voucher no.")
    movement_date = forms.DateField(initial=timezone.localdate, widget=AppDateInput(), label="Transferred date")
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

class ReturnForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True), widget=asset_picker())
    include_accessories = forms.BooleanField(required=False, initial=True, label="Also return the accessories attached to this item")
    stock_location = forms.ModelChoiceField(queryset=Location.objects.filter(is_stock_location=True, is_active=True), label="Returned stock (stores location)")
    returned_by = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False, widget=SearchableSelect(), label="Return from name")
    return_from_division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, label="Return from division", help_text="Leave blank to take the returning employee's division.")
    voucher_number = forms.CharField(max_length=100, required=False, label="Return voucher no.")
    movement_date = forms.DateField(initial=timezone.localdate, widget=AppDateInput(), label="Return voucher date")
    return_clause = forms.ChoiceField(choices=[("", "---------")] + list(AssetMovement.ReturnClause.choices), label="Return clause")
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
