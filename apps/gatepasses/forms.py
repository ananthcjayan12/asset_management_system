from django import forms
from apps.assets.access import employee_assets
from apps.assets.models import Asset
from apps.core.models import Division
from apps.core.widgets import AppDateInput
from .models import GatePass

ELIGIBLE_ASSETS = Asset.objects.filter(is_active=True).exclude(current_status__in=[Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT])

def assets_visible_to(user):
    """Requesters see only items registered in their name or their division; Stores and superusers see all."""
    if manages_gatepass_assets(user):
        return ELIGIBLE_ASSETS
    return employee_assets(ELIGIBLE_ASSETS, getattr(user, "employee", None), include_division=True)


def manages_gatepass_assets(user):
    return (user.is_superuser or user.has_perm("gatepasses.approve_gatepass")
            or user.has_perm("assets.change_asset"))

class GatePassForm(forms.ModelForm):
    assets = forms.ModelMultipleChoiceField(queryset=ELIGIBLE_ASSETS, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = GatePass
        fields = ["gatepass_type", "division", "purpose", "destination", "expected_return_date", "remarks", "attachment"]
        widgets = {"expected_return_date": AppDateInput(), "purpose": forms.Textarea(attrs={"rows": 3}), "remarks": forms.Textarea(attrs={"rows": 2})}
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assets"].queryset = assets_visible_to(user).select_related("current_custodian")
        employee = getattr(user, "employee", None)
        if employee and employee.division_id and not manages_gatepass_assets(user):
            self.fields["division"].queryset = Division.objects.filter(pk=employee.division_id)
            self.fields["division"].initial = employee.division_id
            self.fields["division"].required = True
    def clean(self):
        cleaned = super().clean()
        if cleaned.get("gatepass_type") == GatePass.Type.TEMPORARY and not cleaned.get("expected_return_date"):
            self.add_error("expected_return_date", "Expected return date is required for a temporary gate pass.")
        assets = cleaned.get("assets")
        if assets:
            divisions = {asset.division_id or getattr(asset.current_custodian, "division_id", None) for asset in assets}
            divisions.discard(None)
            division = cleaned.get("division")
            if division and divisions - {division.pk} or len(divisions) > 1:
                self.add_error("assets", "Select assets from the same division as the gate pass.")
            elif not division and len(divisions) == 1:
                cleaned["division"] = Division.objects.get(pk=next(iter(divisions)))
        return cleaned

class RejectForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Reason for rejection")
