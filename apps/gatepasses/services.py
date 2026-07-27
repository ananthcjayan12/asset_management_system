from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.services import audit
from apps.movements.models import AssetMovement
from .models import GatePass

@transaction.atomic
def approve_gatepass(*, gatepass, user):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.status != GatePass.Status.REQUESTED:
        raise ValidationError("Only requested gate passes can be approved.")
    if not gatepass.items.exists():
        raise ValidationError("A gate pass must contain at least one asset.")
    gatepass.status = GatePass.Status.STORES_APPROVED
    gatepass.stores_marked_by = user
    gatepass.save(update_fields=["status", "stores_marked_by", "updated_at"])
    audit(actor=user, action="GATEPASS_APPROVE", obj=gatepass, description=f"Approved {gatepass.gatepass_no}")
    return gatepass

@transaction.atomic
def mark_outward(*, gatepass, user):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.status != GatePass.Status.STORES_APPROVED:
        raise ValidationError("Gate pass must be approved by Stores before outward scanning.")
    for item in gatepass.items.select_related("asset"):
        asset = Asset.objects.select_for_update().get(pk=item.asset_id)
        AssetMovement.objects.create(
            asset=asset, movement_type=AssetMovement.Type.GATE_OUT,
            from_location=asset.current_location, from_employee=asset.current_custodian,
            movement_date=timezone.localdate(), approved_by=user,
            voucher_number=gatepass.gatepass_no, remarks=gatepass.purpose,
        )
        asset.current_status = Asset.Status.OUTSIDE
        asset.save(update_fields=["current_status", "updated_at"])
        item.outward_scanned = True
        item.save(update_fields=["outward_scanned", "updated_at"])
    gatepass.status = GatePass.Status.CLOSED if gatepass.gatepass_type == GatePass.Type.PERMANENT else GatePass.Status.OUTWARD
    gatepass.security_out_by = user
    gatepass.outward_at = timezone.now()
    gatepass.save(update_fields=["status", "security_out_by", "outward_at", "updated_at"])
    audit(actor=user, action="GATE_OUT", obj=gatepass, description=f"Marked {gatepass.gatepass_no} outward")
    return gatepass

@transaction.atomic
def mark_inward(*, gatepass, user):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.gatepass_type != GatePass.Type.TEMPORARY:
        raise ValidationError("Only temporary gate passes can be marked inward.")
    if gatepass.status != GatePass.Status.OUTWARD:
        raise ValidationError("Only outward gate passes can be marked inward.")
    for item in gatepass.items.select_related("asset"):
        asset = Asset.objects.select_for_update().get(pk=item.asset_id)
        AssetMovement.objects.create(
            asset=asset, movement_type=AssetMovement.Type.GATE_IN,
            to_location=asset.current_location, to_employee=asset.current_custodian,
            movement_date=timezone.localdate(), approved_by=user,
            voucher_number=gatepass.gatepass_no, remarks="Returned through security",
        )
        asset.current_status = Asset.Status.ASSIGNED if asset.current_custodian else Asset.Status.IN_STOCK
        asset.save(update_fields=["current_status", "updated_at"])
        item.inward_scanned = True
        item.save(update_fields=["inward_scanned", "updated_at"])
    gatepass.status = GatePass.Status.CLOSED
    gatepass.security_in_by = user
    gatepass.inward_at = timezone.now()
    gatepass.save(update_fields=["status", "security_in_by", "inward_at", "updated_at"])
    audit(actor=user, action="GATE_IN", obj=gatepass, description=f"Marked {gatepass.gatepass_no} inward and closed")
    return gatepass
