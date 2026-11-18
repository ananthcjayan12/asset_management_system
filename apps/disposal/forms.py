from django import forms
from apps.core.widgets import AppDateInput, SearchableSelect
from .models import DisposalRecord
class DisposalForm(forms.ModelForm):
    class Meta:
        model = DisposalRecord
        exclude = ["approved_by"]
        widgets = {"asset": SearchableSelect(), "write_off_om_date": AppDateInput(), "passout_date": AppDateInput(), "remarks": forms.Textarea(attrs={"rows": 3})}
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        # Stores and DA can classify returned assets into lots.
        if not user.has_perm("disposal.classify_lot"):
            self.fields["lot_name"].disabled = True
            self.fields["lot_name"].help_text = "Lot classification is available to SO-Stores and DA."
