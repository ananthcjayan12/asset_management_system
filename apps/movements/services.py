from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.services import audit
from .models import AssetMovement

@transaction.atomic
def transfer_asset(*, asset, destination, recipient, approved_by, voucher_number="", movement_date=None, remarks=""):
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if asset.current_status in {Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT}:
        raise ValidationError("A disposed, written-off, or passed-out asset cannot be transferred.")
    if destination is None:
        raise ValidationError("A destination location is required.")
    movement = AssetMovement.objects.create(
        asset=asset, movement_type=AssetMovement.Type.TRANSFER,
        from_location=asset.current_location, to_location=destination,
        from_employee=asset.current_custodian, to_employee=recipient,
        voucher_number=voucher_number, movement_date=movement_date or timezone.localdate(),
        approved_by=approved_by, remarks=remarks, transfer=True,
        transfer_from_name=getattr(asset.current_custodian, "name", ""),
        transfer_from_id=getattr(asset.current_custodian, "employee_id", ""),
        transfer_to_name=getattr(recipient, "name", ""),
        transfer_to_id=getattr(recipient, "employee_id", ""),
        transfer_voucher_date=movement_date or timezone.localdate(),
    )
    asset.current_location = destination
    asset.current_custodian = recipient
    asset.current_status = Asset.Status.ASSIGNED if recipient else Asset.Status.IN_STOCK
    asset.save(update_fields=["current_location", "current_custodian", "current_status", "updated_at"])
    audit(actor=approved_by, action="TRANSFER", obj=asset, description=f"Transferred {asset.asset_code} to {destination}", metadata={"movement_id": movement.pk})
    return movement

@transaction.atomic
def return_asset(*, asset, stock_location, returned_by, approved_by, voucher_number="", movement_date=None, return_clause="", remarks=""):
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if not stock_location or not stock_location.is_stock_location:
        raise ValidationError("Return destination must be marked as a stock location.")
    movement = AssetMovement.objects.create(
        asset=asset, movement_type=AssetMovement.Type.RETURN,
        from_location=asset.current_location, to_location=stock_location,
        from_employee=asset.current_custodian, to_employee=None,
        voucher_number=voucher_number, movement_date=movement_date or timezone.localdate(),
        approved_by=approved_by, remarks=remarks, returned_stock=True,
        return_from_name=getattr(returned_by, "name", "") or getattr(asset.current_custodian, "name", ""),
        return_voucher_date=movement_date or timezone.localdate(),
        return_clause=return_clause,
        return_from_division=getattr(returned_by, "division", None) or getattr(asset.current_custodian, "division", None),
    )
    asset.current_location = stock_location
    asset.current_custodian = None
    asset.current_status = Asset.Status.IN_STOCK
    asset.save(update_fields=["current_location", "current_custodian", "current_status", "updated_at"])
    audit(actor=approved_by, action="RETURN", obj=asset, description=f"Returned {asset.asset_code} to stock", metadata={"movement_id": movement.pk})
    return movement
