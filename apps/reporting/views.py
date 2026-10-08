import csv
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from apps.assets.models import Asset
from apps.gatepasses.models import GatePass
from .forms import GROUPINGS, AssetReportForm

STATUS_LABELS = dict(Asset.Status.choices)

def report_queryset(request):
    form = AssetReportForm(request.GET or None)
    qs = Asset.objects.select_related("current_location__building__centre", "current_custodian", "division", "procurement__supplier")
    return form, form.filter(qs)

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def dashboard(request):
    by_status = [{"label": STATUS_LABELS.get(r["current_status"], r["current_status"]), "count": r["count"]} for r in Asset.objects.values("current_status").annotate(count=Count("id")).order_by("current_status")]
    by_type = Asset.objects.values("inventory_type").annotate(count=Count("id")).order_by("inventory_type")
    by_location = Asset.objects.values("current_location__name").annotate(count=Count("id")).order_by("-count")[:20]
    acquisition = Asset.objects.exclude(procurement__amount__isnull=True).values("procurement__currency").annotate(total=Sum("procurement__amount")).order_by("procurement__currency")
    return render(request, "reporting/dashboard.html", {"by_status": by_status, "by_type": by_type, "by_location": by_location, "acquisition": acquisition, "overdue_gatepasses": GatePass.objects.filter(status=GatePass.Status.OUTWARD, expected_return_date__lt=timezone.localdate()).select_related("division")})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_report(request):
    form, qs = report_queryset(request)
    groups, heading = [], ""
    group_by = form.cleaned_data.get("group_by") if form.is_valid() else ""
    if group_by:
        fields, heading = GROUPINGS[group_by]
        for row in qs.order_by().values(*fields).annotate(count=Count("id")).order_by(*fields):
            parts = [str(row[f]) for f in fields if row[f] not in (None, "")]
            label = " / ".join(parts) or "Not recorded"
            if group_by == "status":
                label = STATUS_LABELS.get(row["current_status"], label)
            groups.append({"label": label, "count": row["count"]})
    query = request.GET.copy(); query.pop("page", None)
    page = Paginator(qs, 100).get_page(request.GET.get("page"))
    return render(request, "reporting/asset_report.html", {"form": form, "page": page, "groups": groups, "heading": heading, "total": qs.count(), "query": query.urlencode()})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def assets_csv(request):
    _, qs = report_queryset(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="asset-register.csv"'
    w = csv.writer(response)
    w.writerow(["SL No", "Transaction ID", "RFID Code", "Type of Inventory", "Description", "Make", "Model", "Serial No", "Main Item", "Status", "Centre", "Building", "Location", "Room", "Division", "Custodian", "PO No", "Supplier", "Currency", "Amount / Unit Rate", "Bill Value", "DRR No", "GRIN No", "Remarks"])
    for a in qs.select_related("parent_asset"):
        p = getattr(a, "procurement", None)
        loc = a.current_location
        building = getattr(loc, "building", None)
        w.writerow([a.sl_no or "", a.transaction_id, a.asset_code or "", a.inventory_type, a.brief_description, a.make, a.model, a.item_sl_no, a.parent_asset.display_code if a.parent_asset else "", a.get_current_status_display(), getattr(getattr(building, "centre", None), "name", ""), getattr(building, "name", ""), getattr(loc, "name", ""), getattr(loc, "room_no", ""), getattr(a.division, "name", ""), a.current_custodian or "", getattr(p, "po_no", ""), getattr(getattr(p, "supplier", None), "name", ""), getattr(p, "currency", ""), getattr(p, "amount", ""), getattr(p, "bill_value", ""), getattr(p, "drr_no", ""), getattr(p, "grin_no", ""), a.remarks])
    return response
