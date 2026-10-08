from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.services import audit
from .models import AssetMovement

CLOSED_STATUSES = {Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT}

def _place(location):
    building = getattr(getattr(location, "building", None), "name", "")
    return {"building": building, "room": getattr(location, "room_no", "")}

@transaction.atomic
def transfer_asset(*, asset, destination, recipient, approved_by, voucher_number="", movement_date=None, remarks="", division=None, inventory_type="", include_accessories=True):
    asset = Asset.objects.select_for_update().select_related("current_location__building", "division").get(pk=asset.pk)
    if asset.current_status in CLOSED_STATUSES:
        raise ValidationError("A disposed, written-off, or passed-out asset cannot be transferred.")
    if destination is None:
        raise ValidationError("A destination location is required.")
    movement_date = movement_date or timezone.localdate()
    new_division = division or getattr(recipient, "division", None) or destination.division or asset.division
    new_type = inventory_type or asset.inventory_type
    before, after = _place(asset.current_location), _place(destination)
    movement = AssetMovement.objects.create(
        asset=asset, movement_type=AssetMovement.Type.TRANSFER,
        from_location=asset.current_location, to_location=destination,
        from_employee=asset.current_custodian, to_employee=recipient,
        from_division=asset.division, to_division=new_division,
        from_inventory_type=asset.inventory_type, to_inventory_type=new_type,
        from_building=before["building"], to_building=after["building"],
        from_room=before["room"], to_room=after["room"],
        voucher_number=voucher_number, movement_date=movement_date,
        approved_by=approved_by, remarks=remarks, transfer=True,
        transfer_from_name=getattr(asset.current_custodian, "name", ""),
        transfer_from_id=getattr(asset.current_custodian, "employee_id", ""),
        transfer_to_name=getattr(recipient, "name", ""),
        transfer_to_id=getattr(recipient, "employee_id", ""),
        transfer_voucher_date=movement_date,
    )
    asset.current_location = destination
    asset.current_custodian = recipient
    asset.division = new_division
    asset.inventory_type = new_type
    asset.current_status = Asset.Status.ASSIGNED if recipient else Asset.Status.IN_STOCK
    asset.save(update_fields=["current_location", "current_custodian", "division", "inventory_type", "current_status", "updated_at"])
    audit(actor=approved_by, action="TRANSFER", obj=asset, description=f"Transferred {asset.display_code} to {destination}", metadata={"movement_id": movement.pk})
    if include_accessories:
        for accessory in asset.accessories.filter(is_active=True).exclude(current_status__in=CLOSED_STATUSES):
            transfer_asset(asset=accessory, destination=destination, recipient=recipient, approved_by=approved_by, voucher_number=voucher_number, movement_date=movement_date, remarks=remarks or f"Moved with main item {asset.display_code}", division=new_division, inventory_type=inventory_type, include_accessories=False)
    return movement

@transaction.atomic
def return_asset(*, asset, stock_location, returned_by, approved_by, voucher_number="", movement_date=None, return_clause="", remarks="", return_from_division=None, include_accessories=True):
    asset = Asset.objects.select_for_update().select_related("current_location__building", "division").get(pk=asset.pk)
    if not stock_location or not stock_location.is_stock_location:
        raise ValidationError("Return destination must be marked as a stock location.")
    movement_date = movement_date or timezone.localdate()
    from_division = return_from_division or getattr(returned_by, "division", None) or getattr(asset.current_custodian, "division", None) or asset.division
    before, after = _place(asset.current_location), _place(stock_location)
    movement = AssetMovement.objects.create(
        asset=asset, movement_type=AssetMovement.Type.RETURN,
        from_location=asset.current_location, to_location=stock_location,
        from_employee=asset.current_custodian, to_employee=None,
        from_division=asset.division, to_division=stock_location.division or asset.division,
        from_inventory_type=asset.inventory_type, to_inventory_type=asset.inventory_type,
        from_building=before["building"], to_building=after["building"],
        from_room=before["room"], to_room=after["room"],
        voucher_number=voucher_number, movement_date=movement_date,
        approved_by=approved_by, remarks=remarks, returned_stock=True,
        return_from_name=getattr(returned_by, "name", "") or getattr(asset.current_custodian, "name", ""),
        return_voucher_date=movement_date,
        return_clause=return_clause,
        return_from_division=from_division,
    )
    asset.current_location = stock_location
    asset.current_custodian = None
    asset.division = stock_location.division or asset.division
    asset.current_status = Asset.Status.IN_STOCK
    asset.save(update_fields=["current_location", "current_custodian", "division", "current_status", "updated_at"])
    audit(actor=approved_by, action="RETURN", obj=asset, description=f"Returned {asset.display_code} to stock", metadata={"movement_id": movement.pk})
    if include_accessories:
        for accessory in asset.accessories.filter(is_active=True).exclude(current_status__in=CLOSED_STATUSES):
            return_asset(asset=accessory, stock_location=stock_location, returned_by=returned_by, approved_by=approved_by, voucher_number=voucher_number, movement_date=movement_date, return_clause=return_clause, remarks=remarks or f"Returned with main item {asset.display_code}", return_from_division=return_from_division, include_accessories=False)
    return movement
