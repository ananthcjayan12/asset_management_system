import csv
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from apps.assets.models import Asset
from apps.gatepasses.models import GatePass

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def dashboard(request):
    by_status = Asset.objects.values("current_status").annotate(count=Count("id")).order_by("current_status")
    by_location = Asset.objects.values("current_location__name").annotate(count=Count("id")).order_by("-count")[:20]
    acquisition = Asset.objects.aggregate(total=Sum("procurement__amount"))["total"] or 0
    return render(request, "reporting/dashboard.html", {"by_status": by_status, "by_location": by_location, "acquisition": acquisition, "overdue_gatepasses": GatePass.objects.filter(status=GatePass.Status.OUTWARD, expected_return_date__lt=timezone.localdate()).select_related("division")})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def assets_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="asset-register.csv"'
    w = csv.writer(response)
    w.writerow(["Asset Code", "Transaction ID", "Description", "Make", "Model", "Serial No", "Status", "Location", "Custodian", "PO No", "Supplier", "Amount", "Remarks"])
    for a in Asset.objects.select_related("current_location", "current_custodian", "procurement__supplier"):
        p = getattr(a, "procurement", None)
        w.writerow([a.asset_code, a.transaction_id, a.brief_description, a.make, a.model, a.item_sl_no, a.get_current_status_display(), a.current_location or "", a.current_custodian or "", getattr(p, "po_no", ""), getattr(getattr(p, "supplier", None), "name", ""), getattr(p, "amount", ""), a.remarks])
    return response
