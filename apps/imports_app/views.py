from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import ImportUploadForm
from .models import ImportBatch
from .services import confirm_batch, validate_batch

@login_required
@permission_required("imports_app.view_importbatch", raise_exception=True)
def batch_list(request):
    return render(request, "imports/batch_list.html", {"batches": ImportBatch.objects.select_related("uploaded_by")[:50]})

@login_required
@permission_required("imports_app.add_importbatch", raise_exception=True)
def upload(request):
    form = ImportUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        batch = form.save(commit=False); batch.uploaded_by = request.user; batch.save()
        try: validate_batch(batch)
        except Exception as exc:
            batch.status = ImportBatch.Status.FAILED
            batch.notes = (batch.notes + "\nValidation error: " + str(exc)).strip()
            batch.save(update_fields=["status", "notes", "updated_at"])
            messages.error(request, f"The workbook could not be processed: {exc}")
        else: messages.success(request, f"Validated {batch.total_rows} rows.")
        return redirect("imports_app:detail", pk=batch.pk)
    return render(request, "shared/form.html", {"form": form, "title": "Upload asset Excel workbook", "submit_label": "Upload and validate"})

@login_required
@permission_required("imports_app.view_importbatch", raise_exception=True)
def detail(request, pk):
    batch = get_object_or_404(ImportBatch.objects.select_related("uploaded_by"), pk=pk)
    return render(request, "imports/batch_detail.html", {"batch": batch, "rows": batch.rows.all()[:200]})

@login_required
@permission_required("imports_app.change_importbatch", raise_exception=True)
def confirm(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk)
    if request.method == "POST":
        try: confirm_batch(batch, request.user)
        except Exception as exc: messages.error(request, str(exc))
        else: messages.success(request, f"Imported {batch.valid_rows} assets.")
    return redirect("imports_app:detail", pk=pk)
