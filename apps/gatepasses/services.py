from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.assets.models import Asset
from apps.core.services import audit
from apps.movements.models import AssetMovement
from .models import GatePass

def user_division(user):
    return getattr(getattr(user, "employee", None), "division", None)

def check_division_admin(gatepass, user):
    """A division admin may only act on gate passes of their own division."""
    if user.is_superuser or not gatepass.division_id:
        return
    division = user_division(user)
    if division is None or division.pk != gatepass.division_id:
        raise ValidationError("You can only act on gate passes of your own division.")

@transaction.atomic
def division_approve_gatepass(*, gatepass, user):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.status != GatePass.Status.REQUESTED:
        raise ValidationError("Only requested gate passes can be approved by the division.")
    check_division_admin(gatepass, user)
    if not gatepass.items.exists():
        raise ValidationError("A gate pass must contain at least one asset.")
    gatepass.status = GatePass.Status.DIVISION_APPROVED
    gatepass.division_approved_by = user
    gatepass.save(update_fields=["status", "division_approved_by", "updated_at"])
    audit(actor=user, action="GATEPASS_DIVISION_APPROVE", obj=gatepass, description=f"Division approved {gatepass.gatepass_no}")
    return gatepass

@transaction.atomic
def reject_gatepass(*, gatepass, user, reason=""):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.status == GatePass.Status.REQUESTED:
        if not user.has_perm("gatepasses.division_approve_gatepass"):
            raise ValidationError("Only the division admin can reject a newly requested gate pass.")
        check_division_admin(gatepass, user)
    elif gatepass.status == GatePass.Status.DIVISION_APPROVED:
        if not user.has_perm("gatepasses.approve_gatepass"):
            raise ValidationError("Only Stores can reject a division-approved gate pass.")
    else:
        raise ValidationError("Only gate passes awaiting approval can be rejected.")
    gatepass.status = GatePass.Status.REJECTED
    gatepass.rejected_by = user
    gatepass.rejected_at = timezone.now()
    gatepass.rejection_reason = reason.strip()
    gatepass.save(update_fields=["status", "rejected_by", "rejected_at", "rejection_reason", "updated_at"])
    audit(actor=user, action="GATEPASS_REJECT", obj=gatepass, description=f"Rejected {gatepass.gatepass_no}: {gatepass.rejection_reason or 'no reason given'}")
    return gatepass

@transaction.atomic
def approve_gatepass(*, gatepass, user):
    gatepass = GatePass.objects.select_for_update().get(pk=gatepass.pk)
    if gatepass.status != GatePass.Status.DIVISION_APPROVED:
        raise ValidationError("The division admin must approve the gate pass before Stores approval.")
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
    gatepass.status = GatePass.Status.OUTWARD
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
