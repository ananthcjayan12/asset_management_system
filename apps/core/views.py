from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from apps.assets.models import Asset
from apps.gatepasses.models import GatePass
from .models import AuditEvent

@login_required
def dashboard(request):
    status_counts = {row["current_status"]: row["count"] for row in Asset.objects.values("current_status").annotate(count=Count("id"))}
    cards = [
        ("Total assets", Asset.objects.filter(is_active=True).count()),
        ("Issued", status_counts.get(Asset.Status.ASSIGNED, 0)),
        ("In stock", status_counts.get(Asset.Status.IN_STOCK, 0)),
        ("Outside", status_counts.get(Asset.Status.OUTSIDE, 0)),
        ("Under disposal", status_counts.get(Asset.Status.UNDER_DISPOSAL, 0)),
        ("Gate passes awaiting return", GatePass.objects.filter(status=GatePass.Status.OUTWARD, gatepass_type=GatePass.Type.TEMPORARY).count()),
    ]
    return render(request, "core/dashboard.html", {"cards": cards, "recent_events": AuditEvent.objects.select_related("actor")[:10], "recent_gatepasses": GatePass.objects.select_related("division")[:8]})
