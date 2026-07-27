from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
import qrcode
from apps.core.services import audit
from .forms import AssetForm, ProcurementForm, InstallationForm
from .models import Asset, Procurement, Installation

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    qs = Asset.objects.select_related("current_location", "current_custodian")
    if q:
        qs = qs.filter(Q(asset_code__icontains=q) | Q(transaction_id__icontains=q) | Q(brief_description__icontains=q) | Q(item_sl_no__icontains=q) | Q(make__icontains=q) | Q(model__icontains=q))
    if status: qs = qs.filter(current_status=status)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    template = "assets/_asset_table.html" if request.headers.get("HX-Request") else "assets/asset_list.html"
    return render(request, template, {"page": page, "q": q, "status": status, "statuses": Asset.Status.choices})

@login_required
@permission_required("assets.view_asset", raise_exception=True)
def asset_detail(request, pk):
    asset = get_object_or_404(Asset.objects.select_related("current_location", "current_custodian", "procurement__supplier", "installation"), pk=pk)
    return render(request, "assets/asset_detail.html", {"asset": asset, "movements": asset.movements.select_related("from_location", "to_location", "from_employee", "to_employee")[:20]})

@login_required
@permission_required("assets.add_asset", raise_exception=True)
@transaction.atomic
def asset_create(request):
    asset_form = AssetForm(request.POST or None)
    procurement_form = ProcurementForm(request.POST or None, prefix="proc")
    installation_form = InstallationForm(request.POST or None, prefix="install")
    if request.method == "POST" and all([asset_form.is_valid(), procurement_form.is_valid(), installation_form.is_valid()]):
        asset = asset_form.save()
        procurement = procurement_form.save(commit=False); procurement.asset = asset; procurement.save()
        installation = installation_form.save(commit=False); installation.asset = asset; installation.save()
        audit(actor=request.user, action="CREATE", obj=asset, description=f"Created asset {asset.asset_code}")
        messages.success(request, "Asset created successfully.")
        return redirect("assets:detail", pk=asset.pk)
    return render(request, "assets/asset_form.html", {"asset_form": asset_form, "procurement_form": procurement_form, "installation_form": installation_form, "title": "Register asset"})

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
        audit(actor=request.user, action="UPDATE", obj=asset, description=f"Updated asset {asset.asset_code}")
        messages.success(request, "Asset updated successfully.")
        return redirect("assets:detail", pk=asset.pk)
    return render(request, "assets/asset_form.html", {"asset_form": asset_form, "procurement_form": procurement_form, "installation_form": installation_form, "title": f"Edit {asset.asset_code}"})

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
