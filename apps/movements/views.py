from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from .forms import TransferForm, ReturnForm
from .models import AssetMovement
from .services import transfer_asset, return_asset

@login_required
@permission_required("movements.view_assetmovement", raise_exception=True)
def movement_list(request):
    page = Paginator(AssetMovement.objects.select_related("asset", "from_location", "to_location", "approved_by"), 30).get_page(request.GET.get("page"))
    return render(request, "movements/movement_list.html", {"page": page})

@login_required
@permission_required("movements.approve_assetmovement", raise_exception=True)
def transfer(request):
    form = TransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            movement = transfer_asset(approved_by=request.user, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"Asset {movement.asset.asset_code} transferred.")
            return redirect("assets:detail", pk=movement.asset_id)
    return render(request, "shared/form.html", {"form": form, "title": "Transfer asset", "submit_label": "Execute transfer"})

@login_required
@permission_required("movements.approve_assetmovement", raise_exception=True)
def return_to_stock(request):
    form = ReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            movement = return_asset(approved_by=request.user, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"Asset {movement.asset.asset_code} returned to stock.")
            return redirect("assets:detail", pk=movement.asset_id)
    return render(request, "shared/form.html", {"form": form, "title": "Return asset to stock", "submit_label": "Record return"})
