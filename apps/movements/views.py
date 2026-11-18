from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MovementActionForm, ReturnForm, TransferForm
from .models import AssetMovement
from .services import action_for, advance_movement, initiate_return_request, initiate_transfer_request


@login_required
@permission_required("movements.view_assetmovement", raise_exception=True)
def movement_list(request):
    qs = AssetMovement.objects.select_related(
        "asset", "from_location", "to_location", "from_employee", "to_employee",
        "from_division", "to_division", "approved_by",
    )
    user = request.user
    employee = getattr(user, "employee", None)
    if not (user.has_perm("movements.approve_assetmovement") or user.groups.filter(
        name__in=["Auditor", "Report Viewer", "Director"]
    ).exists()):
        scope = Q(initiated_by=user)
        if employee:
            scope |= Q(from_employee=employee) | Q(to_employee=employee)
            if employee.division_id and user.has_perm("movements.hod_approve_movement"):
                scope |= Q(from_division_id=employee.division_id) | Q(to_division_id=employee.division_id)
        qs = qs.filter(scope)
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    for movement in page:
        movement.action_label = action_for(movement, user)
    return render(request, "movements/movement_list.html", {"page": page})


def movement_request(request, form_class, service, title):
    form = form_class(request.POST or None, initial={"asset": request.GET.get("asset")}, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            service(user=request.user, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Request submitted to Dept HOD.")
            return redirect("movements:list")
    return render(request, "movements/movement_form.html", {"form": form, "title": title, "submit_label": "Submit request"})


@login_required
@permission_required("movements.initiate_transfer", raise_exception=True)
def transfer(request):
    return movement_request(request, TransferForm, initiate_transfer_request, "Transfer asset")


@login_required
@permission_required("movements.initiate_return", raise_exception=True)
def return_to_stock(request):
    return movement_request(request, ReturnForm, initiate_return_request, "Return asset to stock")


@login_required
def movement_action(request, pk):
    movement = get_object_or_404(AssetMovement, pk=pk)
    label = action_for(movement, request.user)
    if not label:
        raise PermissionDenied
    reject = request.GET.get("reject") == "1"
    label = "Reject request" if reject else label
    form = MovementActionForm(request.POST if request.method == "POST" else None, movement=movement, reject=reject)
    if request.method == "POST" and form.is_valid():
        try:
            advance_movement(
                movement=movement, user=request.user, expected_status=request.POST.get("status"),
                data=form.cleaned_data, reject=reject,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Movement request updated.")
            return redirect("movements:list")
    return render(request, "movements/movement_action.html", {"form": form, "movement": movement, "label": label})
