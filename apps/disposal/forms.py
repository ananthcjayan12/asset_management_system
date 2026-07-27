from django import forms
from .models import DisposalRecord
class DateInput(forms.DateInput): input_type = "date"
class DisposalForm(forms.ModelForm):
    class Meta:
        model = DisposalRecord
        exclude = ["approved_by"]
        widgets = {"write_off_om_date": DateInput(), "passout_date": DateInput(), "remarks": forms.Textarea(attrs={"rows": 3})}
