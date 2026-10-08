from django import forms
from django.db.models import Q
from apps.assets.models import Asset
from apps.core.models import Division
from apps.core.widgets import AppDateInput
from .models import GatePass

ELIGIBLE_ASSETS = Asset.objects.filter(is_active=True).exclude(current_status__in=[Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT])

def assets_visible_to(user):
    """Requesters see only items registered in their name or their division; Stores and superusers see all."""
    if user.is_superuser or user.has_perm("gatepasses.approve_gatepass"):
        return ELIGIBLE_ASSETS
    employee = getattr(user, "employee", None)
    if employee is None:
        return ELIGIBLE_ASSETS.none()
    condition = Q(current_custodian=employee)
    if employee.division_id:
        condition |= Q(division_id=employee.division_id)
    return ELIGIBLE_ASSETS.filter(condition)

class GatePassForm(forms.ModelForm):
    assets = forms.ModelMultipleChoiceField(queryset=ELIGIBLE_ASSETS, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = GatePass
        fields = ["gatepass_type", "division", "purpose", "destination", "expected_return_date", "remarks"]
        widgets = {"expected_return_date": AppDateInput(), "purpose": forms.Textarea(attrs={"rows": 3}), "remarks": forms.Textarea(attrs={"rows": 2})}
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assets"].queryset = assets_visible_to(user).select_related("current_custodian")
        employee = getattr(user, "employee", None)
        if employee and employee.division_id and not (user.is_superuser or user.has_perm("gatepasses.approve_gatepass")):
            self.fields["division"].queryset = Division.objects.filter(pk=employee.division_id)
            self.fields["division"].initial = employee.division_id
            self.fields["division"].required = True
    def clean(self):
        cleaned = super().clean()
        if cleaned.get("gatepass_type") == GatePass.Type.TEMPORARY and not cleaned.get("expected_return_date"):
            self.add_error("expected_return_date", "Expected return date is required for a temporary gate pass.")
        return cleaned

class RejectForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Reason for rejection")
