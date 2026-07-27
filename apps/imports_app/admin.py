from django.contrib import admin
from .models import ImportBatch, ImportRow
class RowInline(admin.TabularInline): model = ImportRow; extra = 0; readonly_fields = ("row_number", "validation_status", "validation_errors", "created_asset")
@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "uploaded_by", "total_rows", "valid_rows", "invalid_rows", "created_at")
    inlines = [RowInline]
