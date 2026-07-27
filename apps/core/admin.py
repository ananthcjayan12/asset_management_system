from django.contrib import admin
from .models import Division, Section, SubSection, Location, Employee, Supplier, AuditEvent, Attachment
@admin.register(Division, Section, SubSection, Location, Employee, Supplier, Attachment)
class StandardAdmin(admin.ModelAdmin):
    list_per_page = 50
@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "description")
    list_filter = ("action", "object_type")
    search_fields = ("description", "object_id")
    readonly_fields = ("created_at",)
