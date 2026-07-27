from django.contrib import admin
from .models import GatePass, GatePassItem
class ItemInline(admin.TabularInline): model = GatePassItem; extra = 0
@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ("gatepass_no", "gatepass_type", "status", "division", "requested_by", "created_at")
    list_filter = ("gatepass_type", "status")
    inlines = [ItemInline]
