from django.db.models import Count, Q
from django.utils import timezone

from .models import GatePass


def visible_gatepasses(user):
    qs = GatePass.objects.all()
    if not user.has_perm("gatepasses.view_gatepass"):
        return qs.none()
    if any(user.has_perm(f"gatepasses.{permission}") for permission in (
        "approve_gatepass", "director_approve_gatepass", "security_scan_gatepass",
    )) or user.groups.filter(name__in=["Auditor", "Report Viewer"]).exists():
        return qs
    scope = Q(requested_by=user)
    division_id = getattr(getattr(user, "employee", None), "division_id", None)
    if division_id and user.has_perm("gatepasses.division_approve_gatepass"):
        scope |= Q(division_id=division_id)
    return qs.filter(scope)


def gatepass_summary(user):
    qs = visible_gatepasses(user)
    outward = Q(status=GatePass.Status.OUTWARD)
    overdue = outward & Q(gatepass_type=GatePass.Type.TEMPORARY, expected_return_date__lt=timezone.localdate())
    counts = qs.aggregate(
        gp_returned=Count("pk", filter=Q(status=GatePass.Status.CLOSED)),
        gp_non_return=Count("pk", filter=overdue | (outward & Q(gatepass_type=GatePass.Type.PERMANENT))),
        gp_moved_out=Count("pk", filter=outward),
        gp_moved_in=Count("pk", filter=Q(inward_at__isnull=False)),
    )
    alerts = qs.filter(overdue) if (
        user.has_perm("gatepasses.approve_gatepass") or user.has_perm("gatepasses.security_scan_gatepass")
    ) else ()
    return {
        **counts,
        "overdue_gatepasses": alerts,
        "gatepass_cards": [
            ("Returned", counts["gp_returned"]),
            ("Non-Return (Overdue & Permanent Outward)", counts["gp_non_return"]),
            ("Moved Out", counts["gp_moved_out"]),
            ("Moved In", counts["gp_moved_in"]),
        ],
    }
