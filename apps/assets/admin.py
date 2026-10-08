from django.contrib import admin
from django.db import models
from apps.core.widgets import AppDateInput
from .models import Asset, AssetVerification, Procurement, Installation

DATE_OVERRIDES = {models.DateField: {"widget": AppDateInput}}

class ProcurementInline(admin.StackedInline): model = Procurement; extra = 0; formfield_overrides = DATE_OVERRIDES
class InstallationInline(admin.StackedInline): model = Installation; extra = 0; formfield_overrides = DATE_OVERRIDES
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("sl_no", "transaction_id", "asset_code", "inventory_type", "brief_description", "make", "model", "current_status", "current_location", "current_custodian")
    list_filter = ("inventory_type", "current_status", "make", "current_location")
    search_fields = ("asset_code", "transaction_id", "brief_description", "item_sl_no", "make", "model")
    readonly_fields = ("sl_no", "transaction_id")
    raw_id_fields = ("parent_asset",)
    formfield_overrides = DATE_OVERRIDES
    inlines = [ProcurementInline, InstallationInline]

@admin.register(AssetVerification)
class AssetVerificationAdmin(admin.ModelAdmin):
    list_display = ("verification_date", "asset", "result", "location", "verified_by")
    list_filter = ("result", "verification_date")
    search_fields = ("asset__transaction_id", "asset__asset_code", "asset__brief_description")
    raw_id_fields = ("asset",)
    formfield_overrides = DATE_OVERRIDES
