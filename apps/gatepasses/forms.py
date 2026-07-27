from django import forms
from apps.assets.models import Asset
from .models import GatePass

class DateInput(forms.DateInput): input_type = "date"
class GatePassForm(forms.ModelForm):
    assets = forms.ModelMultipleChoiceField(queryset=Asset.objects.filter(is_active=True).exclude(current_status__in=[Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT]), widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = GatePass
        fields = ["gatepass_type", "division", "purpose", "destination", "expected_return_date", "remarks"]
        widgets = {"expected_return_date": DateInput(), "purpose": forms.Textarea(attrs={"rows": 3}), "remarks": forms.Textarea(attrs={"rows": 2})}
    def clean(self):
        cleaned = super().clean()
        if cleaned.get("gatepass_type") == GatePass.Type.TEMPORARY and not cleaned.get("expected_return_date"):
            self.add_error("expected_return_date", "Expected return date is required for a temporary gate pass.")
        return cleaned
