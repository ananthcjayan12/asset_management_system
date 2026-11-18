from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from .forms import GatePassForm, RejectForm, manages_gatepass_assets
from .queries import gatepass_summary, visible_gatepasses
from .models import GatePass, GatePassItem
from .services import approve_gatepass, director_approve_gatepass, division_approve_gatepass, mark_outward, mark_inward, reject_gatepass

@login_required
@permission_required("gatepasses.view_gatepass", raise_exception=True)
def gatepass_list(request):
    qs = visible_gatepasses(request.user).select_related("division", "requested_by")
    status = request.GET.get("status", "")
    if status: qs = qs.filter(status=status)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "gatepasses/gatepass_list.html", {"page": page, "statuses": GatePass.Status.choices, "selected_status": status, **gatepass_summary(request.user)})

@login_required
@permission_required("gatepasses.view_gatepass", raise_exception=True)
def gatepass_detail(request, pk):
    gatepass = get_object_or_404(visible_gatepasses(request.user).select_related("division", "requested_by", "division_approved_by", "director_approved_by", "rejected_by", "stores_marked_by", "security_out_by", "security_in_by"), pk=pk)
    user = request.user
    division = getattr(getattr(user, "employee", None), "division_id", None)
    can_division_approve = (
        gatepass.status == GatePass.Status.REQUESTED and user.has_perm("gatepasses.division_approve_gatepass")
        and (user.is_superuser or not gatepass.division_id or division == gatepass.division_id)
    )
    can_director_approve = gatepass.status == GatePass.Status.PENDING_DIRECTOR and user.has_perm("gatepasses.director_approve_gatepass")
    can_stores_approve = gatepass.status in {GatePass.Status.DIVISION_APPROVED, GatePass.Status.DIRECTOR_APPROVED} and user.has_perm("gatepasses.approve_gatepass")
    return render(request, "gatepasses/gatepass_detail.html", {
        "gatepass": gatepass, "can_reject": can_division_approve or can_director_approve or can_stores_approve,
        "can_division_approve": can_division_approve, "can_director_approve": can_director_approve,
        "can_stores_approve": can_stores_approve, "reject_form": RejectForm(),
    })


@login_required
@permission_required("gatepasses.view_gatepass", raise_exception=True)
def attachment(request, pk):
    gatepass = get_object_or_404(visible_gatepasses(request.user), pk=pk)
    if not gatepass.attachment:
        raise Http404
    try:
        return FileResponse(gatepass.attachment.open("rb"), as_attachment=True)
    except FileNotFoundError as exc:
        raise Http404 from exc

@login_required
@permission_required("gatepasses.add_gatepass", raise_exception=True)
@transaction.atomic
def gatepass_create(request):
    form = GatePassForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        gatepass = form.save(commit=False); gatepass.requested_by = request.user; gatepass.save()
        GatePassItem.objects.bulk_create([GatePassItem(gatepass=gatepass, asset=a) for a in form.cleaned_data["assets"]])
        messages.success(request, f"Gate pass {gatepass.gatepass_no} submitted.")
        return redirect("gatepasses:detail", pk=gatepass.pk)
    restricted = not manages_gatepass_assets(request.user)
    return render(request, "gatepasses/gatepass_form.html", {"form": form, "title": "Request gate pass", "submit_label": "Submit request", "restricted": restricted})

def _action(request, pk, service, success, permission):
    if request.method != "POST": return redirect("gatepasses:detail", pk=pk)
    gatepass = get_object_or_404(GatePass, pk=pk)
    if not request.user.has_perm(permission):
        raise PermissionDenied
    try: service(gatepass=gatepass, user=request.user)
    except ValidationError as exc: messages.error(request, "; ".join(exc.messages))
    else: messages.success(request, success.format(number=gatepass.gatepass_no))
    return redirect("gatepasses:detail", pk=pk)

@login_required
def division_approve(request, pk): return _action(request, pk, division_approve_gatepass, "{number} approved by the division.", "gatepasses.division_approve_gatepass")
@login_required
def director_approve(request, pk):
    return _action(request, pk, director_approve_gatepass, "{number} approved by the Director.", "gatepasses.director_approve_gatepass")


@login_required
def approve(request, pk): return _action(request, pk, approve_gatepass, "{number} approved by Stores.", "gatepasses.approve_gatepass")
@login_required
def reject(request, pk):
    if request.method != "POST": return redirect("gatepasses:detail", pk=pk)
    gatepass = get_object_or_404(GatePass, pk=pk)
    if not any(request.user.has_perm(f"gatepasses.{perm}") for perm in (
        "division_approve_gatepass", "director_approve_gatepass", "approve_gatepass",
    )):
        raise PermissionDenied
    form = RejectForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Give a reason for rejecting the gate pass.")
        return redirect("gatepasses:detail", pk=pk)
    try: reject_gatepass(gatepass=gatepass, user=request.user, reason=form.cleaned_data["reason"])
    except ValidationError as exc: messages.error(request, "; ".join(exc.messages))
    else: messages.success(request, f"{gatepass.gatepass_no} rejected.")
    return redirect("gatepasses:detail", pk=pk)
@login_required
def outward(request, pk): return _action(request, pk, mark_outward, "{number} marked outward.", "gatepasses.security_scan_gatepass")
@login_required
def inward(request, pk): return _action(request, pk, mark_inward, "{number} marked inward and closed.", "gatepasses.security_scan_gatepass")
