from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from apps.assets.access import visible_assets
from apps.assets.models import Asset
from apps.gatepasses.queries import gatepass_summary, visible_gatepasses
from apps.movements.models import AssetMovement
from .models import AuditEvent

@login_required
def dashboard(request):
    assets = visible_assets(Asset.objects.all(), request.user)
    status_counts = {row["current_status"]: row["count"] for row in assets.values("current_status").annotate(count=Count("id"))}
    cards = [
        ("Total assets", assets.filter(is_active=True).count()),
        ("Issued", status_counts.get(Asset.Status.ASSIGNED, 0)),
        ("In stock", status_counts.get(Asset.Status.IN_STOCK, 0)),
        ("Outside", status_counts.get(Asset.Status.OUTSIDE, 0)),
        ("Under disposal", status_counts.get(Asset.Status.UNDER_DISPOSAL, 0)),
    ]
    recent_events = AuditEvent.objects.select_related("actor")
    if not request.user.has_perm("core.view_auditevent"):
        recent_events = recent_events.filter(actor=request.user)
    completed_returns = AssetMovement.objects.filter(
        initiated_by=request.user, movement_type=AssetMovement.Type.RETURN,
        workflow_status=AssetMovement.WorkflowStatus.COMPLETED,
    ).select_related("asset").order_by("-updated_at")[:5]
    return render(request, "core/dashboard.html", {
        "cards": cards,
        "recent_events": recent_events[:10],
        "recent_gatepasses": visible_gatepasses(request.user).select_related("division")[:8],
        "completed_returns": completed_returns,
        **gatepass_summary(request.user),
    })
