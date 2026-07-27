from django.contrib import admin
from .models import Asset, Procurement, Installation
class ProcurementInline(admin.StackedInline): model = Procurement; extra = 0
class InstallationInline(admin.StackedInline): model = Installation; extra = 0
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("asset_code", "brief_description", "make", "model", "current_status", "current_location", "current_custodian")
    list_filter = ("current_status", "make", "current_location")
    search_fields = ("asset_code", "transaction_id", "brief_description", "item_sl_no", "make", "model")
    inlines = [ProcurementInline, InstallationInline]
