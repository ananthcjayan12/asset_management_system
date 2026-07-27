from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from apps.assets.models import Asset
from apps.core.services import audit
from .forms import DisposalForm
from .models import DisposalRecord

@login_required
@permission_required("disposal.view_disposalrecord", raise_exception=True)
def disposal_list(request):
    return render(request, "disposal/disposal_list.html", {"records": DisposalRecord.objects.select_related("asset")})

@login_required
@permission_required("disposal.add_disposalrecord", raise_exception=True)
@transaction.atomic
def disposal_create(request):
    asset_id = request.GET.get("asset")
    initial = {"asset": asset_id} if asset_id else {}
    form = DisposalForm(request.POST or None, initial=initial)
    # New records always start as Proposed. Approval/final status is a separate authority.
    form.fields.pop("status", None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.status = DisposalRecord.Status.PROPOSED
        record.approved_by = None
        record.save()
        record.asset.current_status = Asset.Status.UNDER_DISPOSAL
        record.asset.save(update_fields=["current_status", "updated_at"])
        audit(actor=request.user, action="DISPOSAL_CREATE", obj=record, description=f"Created disposal record for {record.asset.asset_code}")
        messages.success(request, "Disposal record created as Proposed.")
        return redirect("disposal:list")
    return render(request, "shared/form.html", {"form": form, "title": "Disposal, auction, write-off and passout", "submit_label": "Create proposal"})

@login_required
@permission_required("disposal.change_disposalrecord", raise_exception=True)
@transaction.atomic
def disposal_update(request, pk):
    record = get_object_or_404(DisposalRecord.objects.select_for_update().select_related("asset"), pk=pk)
    previous_status = record.status
    form = DisposalForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        requested_status = form.cleaned_data["status"]
        status_changed = requested_status != previous_status
        if status_changed and not request.user.has_perm("disposal.approve_disposalrecord"):
            form.add_error("status", "You do not have permission to approve or change the disposal status.")
        else:
            record = form.save(commit=False)
            if status_changed:
                record.approved_by = request.user
            record.save()
            mapping = {
                DisposalRecord.Status.PROPOSED: Asset.Status.UNDER_DISPOSAL,
                DisposalRecord.Status.APPROVED: Asset.Status.UNDER_DISPOSAL,
                DisposalRecord.Status.AUCTIONED: Asset.Status.DISPOSED,
                DisposalRecord.Status.WRITTEN_OFF: Asset.Status.WRITTEN_OFF,
                DisposalRecord.Status.PASSED_OUT: Asset.Status.PASSED_OUT,
            }
            record.asset.current_status = mapping[record.status]
            record.asset.save(update_fields=["current_status", "updated_at"])
            audit(actor=request.user, action="DISPOSAL_UPDATE", obj=record, description=f"Updated disposal record for {record.asset.asset_code}; status={record.status}")
            messages.success(request, "Disposal record updated.")
            return redirect("disposal:list")
    return render(request, "shared/form.html", {"form": form, "title": f"Update disposal - {record.asset.asset_code}", "submit_label": "Save changes"})
