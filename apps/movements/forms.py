from django import forms
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.models import Employee, Location

class DateInput(forms.DateInput): input_type = "date"

class TransferForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True))
    destination = forms.ModelChoiceField(queryset=Location.objects.filter(is_active=True))
    recipient = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False)
    voucher_number = forms.CharField(max_length=100, required=False)
    movement_date = forms.DateField(initial=timezone.localdate, widget=DateInput())
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

class ReturnForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_active=True))
    stock_location = forms.ModelChoiceField(queryset=Location.objects.filter(is_stock_location=True, is_active=True))
    returned_by = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), required=False)
    voucher_number = forms.CharField(max_length=100, required=False)
    movement_date = forms.DateField(initial=timezone.localdate, widget=DateInput())
    return_clause = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
