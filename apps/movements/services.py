from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.models import Location
from apps.core.services import audit
from apps.disposal.models import DisposalRecord
from .models import AssetMovement

Status = AssetMovement.WorkflowStatus

CLOSED_STATUSES = {Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT}

def _place(location):
    building = getattr(getattr(location, "building", None), "name", "")
    return {"building": building, "room": getattr(location, "room_no", "")}

@transaction.atomic
def transfer_asset(*, asset, destination, recipient, approved_by, voucher_number="", movement_date=None, remarks="", division=None, inventory_type="", include_accessories=True, request_by=None, existing=None):
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if asset.current_status in CLOSED_STATUSES:
        raise ValidationError("A disposed, written-off, or passed-out asset cannot be transferred.")
    if destination is None:
        raise ValidationError("A destination location is required.")
    movement_date = movement_date or timezone.localdate()
    new_division = division or getattr(recipient, "division", None) or destination.division or asset.division
    new_type = inventory_type or asset.inventory_type
    before, after = _place(asset.current_location), _place(destination)
    movement = existing or AssetMovement.objects.create(
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
        transfer_voucher_date=movement_date, include_accessories=include_accessories,
        previous_asset_status=asset.current_status if request_by else "",
        initiated_by=request_by, workflow_status=Status.PENDING_HOD if request_by else Status.COMPLETED,
    )
    if request_by:
        return movement
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
def return_asset(*, asset, stock_location, approved_by, returned_by=None, voucher_number="", movement_date=None, return_clause="", remarks="", return_from_division=None, include_accessories=True, request_by=None, existing=None, material_category="", return_nature=""):
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if (not stock_location and not request_by) or (stock_location and not stock_location.is_stock_location):
        raise ValidationError("Return destination must be marked as a stock location.")
    movement_date = movement_date or timezone.localdate()
    from_division = return_from_division or getattr(returned_by, "division", None) or getattr(asset.current_custodian, "division", None) or asset.division
    before, after = _place(asset.current_location), _place(stock_location)
    movement = existing or AssetMovement.objects.create(
        asset=asset, movement_type=AssetMovement.Type.RETURN,
        from_location=asset.current_location, to_location=stock_location,
        from_employee=asset.current_custodian, to_employee=None,
        from_division=asset.division, to_division=getattr(stock_location, "division", None) or asset.division,
        from_inventory_type=asset.inventory_type, to_inventory_type=asset.inventory_type,
        from_building=before["building"], to_building=after["building"],
        from_room=before["room"], to_room=after["room"],
        voucher_number=voucher_number, movement_date=movement_date,
        approved_by=approved_by, remarks=remarks, returned_stock=True,
        return_from_name=getattr(returned_by, "name", "") or getattr(asset.current_custodian, "name", ""),
        return_voucher_date=movement_date,
        return_clause=return_clause,
        return_from_division=from_division, include_accessories=include_accessories,
        initiated_by=request_by, workflow_status=Status.PENDING_HOD if request_by else Status.COMPLETED,
        material_category=material_category, return_nature=return_nature,
        previous_asset_status=asset.current_status if request_by else "",
    )
    if request_by:
        asset.current_status = Asset.Status.RETURN_PENDING
        asset.save(update_fields=["current_status", "updated_at"])
        return movement
    asset.current_location = stock_location
    asset.current_custodian = None
    asset.division = stock_location.division or asset.division
    asset.current_status = Asset.Status.IN_STOCK
    asset.save(update_fields=["current_location", "current_custodian", "division", "current_status", "updated_at"])
    audit(actor=approved_by, action="RETURN", obj=asset, description=f"Returned {asset.display_code} to stock", metadata={"movement_id": movement.pk})
    if include_accessories:
        for accessory in asset.accessories.filter(is_active=True).exclude(current_status__in=CLOSED_STATUSES):
            return_asset(asset=accessory, stock_location=stock_location, returned_by=returned_by, approved_by=approved_by, voucher_number=voucher_number, movement_date=movement_date, return_clause=return_clause, remarks=remarks or f"Returned with main item {asset.display_code}", return_from_division=return_from_division, include_accessories=False, material_category=material_category, return_nature=return_nature)
    return movement


def pending_movements(queryset):
    return queryset.exclude(workflow_status__in=[Status.COMPLETED, Status.REJECTED])


def can_request_movement(user, asset, permission):
    if not user.has_perm(f"movements.{permission}"):
        return False
    if user.is_superuser or user.groups.filter(name__in=[
        "System Administrator", "Asset Administrator", "Stores Officer",
    ]).exists():
        return True
    employee = getattr(user, "employee", None)
    return employee is not None and asset.current_custodian_id == employee.pk


def lock_request_asset(asset, user, permission):
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if not can_request_movement(user, asset, permission):
        raise PermissionDenied
    if (not asset.is_active or asset.current_status in CLOSED_STATUSES
            or asset.current_status in {Asset.Status.OUTSIDE, Asset.Status.RETURN_PENDING}
            or pending_movements(asset.movements.all()).exists()):
        raise ValidationError("This asset is unavailable or already has a pending movement.")
    return asset


@transaction.atomic
def initiate_transfer_request(*, asset, user, **data):
    asset = lock_request_asset(asset, user, "initiate_transfer")
    return transfer_asset(asset=asset, approved_by=None, request_by=user, **data)


@transaction.atomic
def initiate_return_request(*, asset, user, **data):
    asset = lock_request_asset(asset, user, "initiate_return")
    if not user.has_perm("movements.so_forward_movement") and not user.has_perm("movements.da_complete_movement"):
        data["returned_by"] = asset.current_custodian
        data["return_from_division"] = asset.division
    return return_asset(asset=asset, approved_by=None, request_by=user, **data)


def action_for(movement, user):
    employee = getattr(user, "employee", None)
    division_id = getattr(employee, "division_id", None)
    status = movement.workflow_status
    is_return = movement.movement_type == AssetMovement.Type.RETURN
    if status in {Status.PENDING_HOD, Status.PENDING_RECEIVING_HOD}:
        required_division = movement.from_division_id if status == Status.PENDING_HOD else movement.to_division_id
        if user.has_perm("movements.hod_approve_movement") and (
            user.is_superuser or (division_id and division_id == required_division)
        ):
            return "Forward to CA" if is_return else "Approve"
    elif status == Status.PENDING_RECIPIENT:
        if user.is_superuser or (
            employee and employee.pk == movement.to_employee_id and user.has_perm("movements.accept_transfer")
        ):
            return "Accept transfer"
    elif status == Status.PENDING_CA and user.has_perm("movements.ca_certify_return"):
        return "Certify return"
    elif status == Status.PENDING_SO and user.has_perm("movements.so_forward_movement"):
        return "Mark to DA"
    elif status == Status.PENDING_DA and user.has_perm("movements.da_complete_movement"):
        return "Complete entry"
    return ""


def update_return_details(movement, data):
    for field in ("return_clause", "material_category", "return_nature"):
        if data.get(field):
            setattr(movement, field, data[field])
    if data.get("remarks"):
        movement.remarks = "\n".join(filter(None, (movement.remarks, data["remarks"])))


def choose_stock_location(movement, location):
    active_stock = Location.objects.filter(is_active=True, is_stock_location=True)
    selected = location or active_stock.filter(pk=movement.to_location_id).first() or active_stock.first()
    if not selected:
        raise ValidationError("Set up an active Stores location before forwarding or completing this return.")
    movement.to_location = selected
    movement.to_division = selected.division or movement.from_division
    place = _place(selected)
    movement.to_building = place["building"]
    movement.to_room = place["room"]


def complete_movement(movement, asset, user, data):
    expected_status = Asset.Status.RETURN_PENDING if movement.movement_type == AssetMovement.Type.RETURN else movement.previous_asset_status
    if (asset.current_status != expected_status or asset.current_custodian_id != movement.from_employee_id
            or asset.current_location_id != movement.from_location_id or asset.division_id != movement.from_division_id):
        raise ValidationError("The asset changed after submission. Reject this request and submit a new one.")
    if movement.include_accessories:
        accessories = asset.accessories.select_for_update().filter(is_active=True).exclude(current_status__in=CLOSED_STATUSES)
        for accessory in accessories.order_by("pk"):
            if accessory.current_status in {Asset.Status.OUTSIDE, Asset.Status.RETURN_PENDING} or pending_movements(accessory.movements.all()).exists():
                raise ValidationError("An attached accessory is outside or has a pending movement.")

    common = {
        "asset": asset, "approved_by": user, "voucher_number": movement.voucher_number,
        "movement_date": movement.movement_date, "remarks": movement.remarks,
        "include_accessories": movement.include_accessories, "existing": movement,
    }
    if movement.movement_type == AssetMovement.Type.RETURN:
        choose_stock_location(movement, data.get("stock_location"))
        return_asset(
            stock_location=movement.to_location, returned_by=movement.from_employee,
            return_from_division=movement.return_from_division, return_clause=movement.return_clause,
            return_nature=movement.return_nature, material_category=movement.material_category, **common,
        )
        lot_name = data.get("lot_name") or (
            f"LOT - {movement.material_category.upper()}"
            if movement.return_nature == AssetMovement.ReturnNature.NON_RETURNABLE else ""
        )
        if lot_name:
            record, created = DisposalRecord.objects.get_or_create(asset=asset, defaults={"lot_name": lot_name})
            if not created and record.status == DisposalRecord.Status.PROPOSED:
                record.lot_name = lot_name
                record.save(update_fields=["lot_name", "updated_at"])
    else:
        transfer_asset(
            destination=movement.to_location, recipient=movement.to_employee,
            division=movement.to_division, inventory_type=movement.to_inventory_type, **common,
        )
    movement.approved_by = user
    movement.da_completed_by = user
    movement.workflow_status = Status.COMPLETED


@transaction.atomic
def advance_movement(*, movement, user, expected_status, data, reject=False):
    asset = Asset.objects.select_for_update().get(pk=movement.asset_id)
    movement = AssetMovement.objects.select_for_update().get(pk=movement.pk)
    if movement.workflow_status != expected_status:
        raise ValidationError("This request has already advanced. Reload the movements list.")
    if not action_for(movement, user):
        raise PermissionDenied
    status = movement.workflow_status
    is_return = movement.movement_type == AssetMovement.Type.RETURN
    if reject:
        movement.workflow_status = Status.REJECTED
        movement.rejected_by = user
        movement.rejection_reason = data["reason"]
        if is_return and asset.current_status == Asset.Status.RETURN_PENDING:
            asset.current_status = movement.previous_asset_status or (
                Asset.Status.ASSIGNED if asset.current_custodian_id else Asset.Status.IN_STOCK
            )
            asset.save(update_fields=["current_status", "updated_at"])
    elif status == Status.PENDING_HOD:
        movement.hod_approved_by = user
        movement.workflow_status = (
            Status.PENDING_CA if is_return else
            Status.PENDING_RECIPIENT if movement.to_employee_id else Status.PENDING_SO
        )
    elif status == Status.PENDING_RECIPIENT:
        movement.recipient_accepted_by = user
        movement.workflow_status = (
            Status.PENDING_RECEIVING_HOD
            if movement.to_division_id and movement.to_division_id != movement.from_division_id
            else Status.PENDING_SO
        )
    elif status == Status.PENDING_RECEIVING_HOD:
        movement.receiving_hod_approved_by = user
        movement.workflow_status = Status.PENDING_SO
    elif status == Status.PENDING_CA:
        update_return_details(movement, data)
        movement.ca_certified_by = user
        movement.workflow_status = Status.PENDING_SO
    elif status == Status.PENDING_SO:
        if is_return:
            update_return_details(movement, data)
            choose_stock_location(movement, data.get("stock_location"))
        movement.so_marked_by = user
        movement.workflow_status = Status.PENDING_DA
    elif status == Status.PENDING_DA:
        complete_movement(movement, asset, user, data)
    movement.save()
    audit(
        actor=user, action="MOVEMENT_WORKFLOW", obj=movement,
        description=f"{asset.display_code}: {movement.get_workflow_status_display()}",
        metadata={"initiating_user_id": movement.initiated_by_id},
    )
    return movement
