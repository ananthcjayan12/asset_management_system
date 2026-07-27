from django import forms
from .models import ImportBatch
class ImportUploadForm(forms.ModelForm):
    class Meta:
        model = ImportBatch
        fields = ["uploaded_file", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}
    def clean_uploaded_file(self):
        f = self.cleaned_data["uploaded_file"]
        if not f.name.lower().endswith(".xlsx"): raise forms.ValidationError("Upload an .xlsx Excel workbook.")
        if f.size > 10 * 1024 * 1024: raise forms.ValidationError("Maximum upload size is 10 MB.")
        return f
