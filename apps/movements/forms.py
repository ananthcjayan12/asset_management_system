from django import forms
from django.urls import reverse_lazy
from django.utils import timezone
from apps.assets.access import employee_assets
from apps.assets.models import Asset
from apps.core.models import Division, Employee, Location
from apps.core.widgets import AppDateInput, SearchableSelect
from .models import AssetMovement

def asset_picker():
    """Searchable asset drop-down that loads the asset's details when chosen."""
    return SearchableSelect(attrs={"hx-get": reverse_lazy("assets:summary"), "hx-trigger": "change, load", "hx-target": "#asset-summary"})

class MovementRequestForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not (user.is_superuser or user.groups.filter(name__in=[
            "System Administrator", "Asset Administrator", "Stores Officer",
        ]).exists()):
            asset_field = self.fields["asset"]
            asset_field.queryset = employee_assets(asset_field.queryset, getattr(user, "employee", None))
            self.fields.pop("returned_by", None)
            self.fields.pop("return_from_division", None)


class TransferForm(MovementRequestForm):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True), widget=asset_picker())
    include_accessories = forms.BooleanField(required=False, initial=True, label="Also transfer the accessories attached to this item")
    destination = forms.ModelChoiceField(queryset=Location.objects.filter(is_active=True), widget=SearchableSelect(), help_text="Choose the new place / building / room.")
    recipient = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False, widget=SearchableSelect(), label="Transfer to (name)")
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, label="New division", help_text="Leave blank to take the recipient's or destination's division.")
    inventory_type = forms.ChoiceField(choices=[("", "Keep current")] + list(Asset.InventoryType.choices), required=False, label="Change PIR/DIR")
    voucher_number = forms.CharField(max_length=100, required=False, label="Transfer voucher no.")
    movement_date = forms.DateField(initial=timezone.localdate, widget=AppDateInput(), label="Transferred date")
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def clean(self):
        data = super().clean()
        recipient, division = data.get("recipient"), data.get("division")
        if recipient and division and recipient.division_id and recipient.division_id != division.pk:
            self.add_error("division", "Choose the receiving employee’s division.")
        return data


class ReturnForm(MovementRequestForm):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True), widget=asset_picker())
    include_accessories = forms.BooleanField(required=False, initial=True, label="Also return the accessories attached to this item")
    stock_location = forms.ModelChoiceField(queryset=Location.objects.filter(is_stock_location=True, is_active=True), required=False, label="Returned stock (stores location)")
    returned_by = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False, widget=SearchableSelect(), label="Return from name")
    return_from_division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, label="Return from division", help_text="Leave blank to take the returning employee's division.")
    voucher_number = forms.CharField(max_length=100, required=False, label="Return voucher no.")
    movement_date = forms.DateField(initial=timezone.localdate, widget=AppDateInput(), label="Return voucher date")
    material_category = forms.ChoiceField(choices=AssetMovement.MaterialCategory.choices)
    return_nature = forms.ChoiceField(choices=AssetMovement.ReturnNature.choices, initial=AssetMovement.ReturnNature.NON_RETURNABLE, label="Return type")
    return_clause = forms.ChoiceField(choices=[("", "---------")] + list(AssetMovement.ReturnClause.choices), label="Return clause")
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class MovementActionForm(forms.Form):
    def __init__(self, *args, movement, reject, **kwargs):
        super().__init__(*args, **kwargs)
        if reject:
            self.fields["reason"] = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Rejection reason")
            return
        if movement.movement_type != AssetMovement.Type.RETURN:
            return
        status = movement.workflow_status
        if status in {AssetMovement.WorkflowStatus.PENDING_CA, AssetMovement.WorkflowStatus.PENDING_SO}:
            for name in ("return_clause", "material_category", "return_nature"):
                field = AssetMovement._meta.get_field(name)
                self.fields[name] = forms.ChoiceField(
                    choices=field.choices, initial=getattr(movement, name), label=field.verbose_name.capitalize(),
                )
            self.fields["remarks"] = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
        if status in {AssetMovement.WorkflowStatus.PENDING_SO, AssetMovement.WorkflowStatus.PENDING_DA}:
            self.fields["stock_location"] = forms.ModelChoiceField(
                queryset=Location.objects.filter(is_active=True, is_stock_location=True),
                required=False, initial=movement.to_location_id, label="Stores location",
            )
        if status == AssetMovement.WorkflowStatus.PENDING_DA:
            self.fields["lot_name"] = forms.CharField(required=False, max_length=150, label="Disposal or auction lot")
