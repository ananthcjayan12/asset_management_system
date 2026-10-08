from datetime import datetime

from django import forms

DISPLAY_DATE_FORMAT = "%d-%m-%Y"


class AppDateInput(forms.DateInput):
    """Compact dd-mm-yyyy field with the calendar button placed right beside it.

    The popup (static/js/datepicker.js) offers month and year drop-downs plus
    previous/next-year buttons so distant dates need no long scrolling.
    """
    input_type = "text"

    def __init__(self, attrs=None):
        base = {"data-datepicker": "", "placeholder": "dd-mm-yyyy", "autocomplete": "off", "class": "date-input"}
        super().__init__(attrs={**base, **(attrs or {})}, format=DISPLAY_DATE_FORMAT)

    def format_value(self, value):
        # Re-displayed form data may hold the ISO string produced below; show it as dd-mm-yyyy.
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), "%Y-%m-%d").strftime(DISPLAY_DATE_FORMAT)
            except ValueError:
                return value
        return super().format_value(value)

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.strptime(value.strip(), DISPLAY_DATE_FORMAT).date().isoformat()
            except ValueError:
                pass
        return value

    class Media:
        css = {"all": ["css/datepicker.css"]}
        js = ["js/datepicker.js"]


class SearchableSelect(forms.Select):
    """Select with a type-to-search box (static/js/app.js)."""

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs={"data-searchable": "", **(attrs or {})}, choices=choices)

    class Media:
        js = ["js/app.js"]
