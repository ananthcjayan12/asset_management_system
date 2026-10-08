import csv
from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.utils import timezone
import qrcode
from apps.core.services import audit
from .forms import AssetForm, ProcurementForm, InstallationForm, VerificationFilterForm, VerificationReportForm
from .models import Asset, AssetVerification, Procurement, Installation

CLOSED_STATUSES = [Asset.Status.DISPOSED, Asset.Status.WRITTEN_OFF, Asset.Status.PASSED_OUT]

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    inventory_type = request.GET.get("inventory_type", "").strip()
    qs = Asset.objects.select_related("current_location__building", "current_custodian", "parent_asset")
    if q:
        qs = qs.filter(Q(asset_code__icontains=q) | Q(transaction_id__icontains=q) | Q(brief_description__icontains=q) | Q(item_sl_no__icontains=q) | Q(make__icontains=q) | Q(model__icontains=q))
    if status: qs = qs.filter(current_status=status)
    if inventory_type: qs = qs.filter(inventory_type=inventory_type)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    template = "assets/_asset_table.html" if request.headers.get("HX-Request") else "assets/asset_list.html"
    return render(request, template, {"page": page, "q": q, "status": status, "statuses": Asset.Status.choices, "inventory_type": inventory_type, "inventory_types": Asset.InventoryType.choices})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_detail(request, pk):
    asset = get_object_or_404(Asset.objects.select_related("current_location__building", "current_custodian", "division", "parent_asset", "procurement__supplier", "procurement__budget", "procurement__budget_classification", "procurement__project_code", "installation"), pk=pk)
    return render(request, "assets/asset_detail.html", {
        "asset": asset,
        "accessories": asset.accessories.select_related("current_location", "current_custodian"),
        "movements": asset.movements.select_related("from_location", "to_location", "from_employee", "to_employee", "from_division", "to_division", "approved_by")[:20],
        "verifications": asset.verifications.select_related("verified_by")[:5],
    })

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_summary(request):
    """Partial used by the transfer/return forms to display the chosen asset's details."""
    asset = Asset.objects.select_related("current_location__building", "current_custodian", "division").filter(pk=request.GET.get("asset") or 0).first()
    return render(request, "assets/_asset_summary.html", {"asset": asset, "accessories": asset.accessories.all() if asset else []})

@login_required
@permission_required("assets.add_asset", raise_exception=True)
@transaction.atomic
def asset_create(request):
    parent = Asset.objects.filter(pk=request.GET.get("parent") or 0).first()
    initial = {}
    if parent:
        initial = {"parent_asset": parent.pk, "inventory_type": parent.inventory_type, "current_status": parent.current_status, "current_location": parent.current_location_id, "current_custodian": parent.current_custodian_id, "division": parent.division_id, "room_in_charge_name": parent.room_in_charge_name, "current_user": parent.current_user}
    asset_form = AssetForm(request.POST or None, initial=initial)
    procurement_form = ProcurementForm(request.POST or None, prefix="proc")
    installation_form = InstallationForm(request.POST or None, prefix="install")
    if request.method == "POST" and all([asset_form.is_valid(), procurement_form.is_valid(), installation_form.is_valid()]):
        asset = asset_form.save()
        procurement = procurement_form.save(commit=False); procurement.asset = asset; procurement.save()
        installation = installation_form.save(commit=False); installation.asset = asset; installation.save()
        audit(actor=request.user, action="CREATE", obj=asset, description=f"Created asset {asset.display_code}")
        messages.success(request, f"Asset created successfully. Transaction ID {asset.transaction_id}, SL No. {asset.sl_no}.")
        return redirect("assets:detail", pk=asset.pk)
    title = f"Add accessory to {parent.display_code}" if parent else "Register asset"
    return render(request, "assets/asset_form.html", {"asset_form": asset_form, "procurement_form": procurement_form, "installation_form": installation_form, "title": title})

@login_required
@permission_required("assets.change_asset", raise_exception=True)
@transaction.atomic
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    procurement, _ = Procurement.objects.get_or_create(asset=asset)
    installation, _ = Installation.objects.get_or_create(asset=asset)
    asset_form = AssetForm(request.POST or None, instance=asset)
    procurement_form = ProcurementForm(request.POST or None, instance=procurement, prefix="proc")
    installation_form = InstallationForm(request.POST or None, instance=installation, prefix="install")
    if request.method == "POST" and all([asset_form.is_valid(), procurement_form.is_valid(), installation_form.is_valid()]):
        asset_form.save(); procurement_form.save(); installation_form.save()
        audit(actor=request.user, action="UPDATE", obj=asset, description=f"Updated asset {asset.display_code}")
        messages.success(request, "Asset updated successfully.")
        return redirect("assets:detail", pk=asset.pk)
    return render(request, "assets/asset_form.html", {"asset_form": asset_form, "procurement_form": procurement_form, "installation_form": installation_form, "title": f"Edit {asset.display_code}", "asset": asset})

def qr_page(request, token):
    if not settings.QR_PAGE_PUBLIC and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    asset = get_object_or_404(Asset.objects.select_related("current_location", "current_custodian"), qr_token=token, is_active=True)
    active_gatepass = asset.gatepass_items.exclude(gatepass__status__in=["CLOSED", "REJECTED"]).select_related("gatepass").first()
    return render(request, "assets/qr_page.html", {"asset": asset, "active_gatepass": active_gatepass.gatepass if active_gatepass else None})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def qr_image(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    url = request.build_absolute_uri(reverse("assets:qr_page", kwargs={"token": asset.qr_token}))
    img = qrcode.make(url)
    buffer = BytesIO(); img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")

@login_required
@permission_required("assets.add_assetverification", raise_exception=True)
@transaction.atomic
def verification_record(request):
    """Physical verification: list the assets expected at a location and mark each available or not."""
    form = VerificationFilterForm(request.GET or None, initial={"verification_date": timezone.localdate()})
    assets = []
    if form.is_valid() and form.cleaned_data["location"]:
        assets = list(Asset.objects.filter(is_active=True, current_location=form.cleaned_data["location"]).exclude(current_status__in=CLOSED_STATUSES).select_related("current_custodian", "parent_asset"))
    if request.method == "POST" and form.is_valid():
        location, on_date = form.cleaned_data["location"], form.cleaned_data["verification_date"]
        saved = 0
        for asset in assets:
            result = request.POST.get(f"result_{asset.pk}")
            if result not in AssetVerification.Result.values:
                continue
            AssetVerification.objects.create(asset=asset, verification_date=on_date, result=result, location=location, verified_by=request.user, remarks=request.POST.get(f"remarks_{asset.pk}", "").strip()[:250])
            saved += 1
        audit(actor=request.user, action="VERIFY", obj=location, description=f"Verified {saved} assets at {location} on {on_date:%d-%m-%Y}")
        messages.success(request, f"Saved verification for {saved} assets.")
        return redirect("assets:verification_list")
    return render(request, "assets/verification_record.html", {"form": form, "assets": assets, "results": AssetVerification.Result.choices})

@login_required
@permission_required("assets.view_assetverification", raise_exception=True)
def verification_list(request):
    form = VerificationReportForm(request.GET or None)
    qs = AssetVerification.objects.select_related("asset", "location__building", "verified_by")
    if form.is_valid():
        data = form.cleaned_data
        if data["date_from"]: qs = qs.filter(verification_date__gte=data["date_from"])
        if data["date_to"]: qs = qs.filter(verification_date__lte=data["date_to"])
        if data["result"]: qs = qs.filter(result=data["result"])
        if data["location"]: qs = qs.filter(location=data["location"])
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="asset-verification.csv"'
        w = csv.writer(response)
        w.writerow(["Verification date", "Transaction ID", "RFID code", "Description", "Location", "Result", "Verified by", "Remarks"])
        for v in qs:
            w.writerow([f"{v.verification_date:%d-%m-%Y}", v.asset.transaction_id, v.asset.asset_code or "", v.asset.brief_description, v.location or "", v.get_result_display(), v.verified_by or "", v.remarks])
        return response
    summary = {row["result"]: row["count"] for row in qs.order_by().values("result").annotate(count=Count("id"))}
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    query = request.GET.copy(); query.pop("page", None)
    return render(request, "assets/verification_list.html", {"form": form, "page": page, "query": query.urlencode(), "available": summary.get(AssetVerification.Result.AVAILABLE, 0), "not_available": summary.get(AssetVerification.Result.NOT_AVAILABLE, 0)})
