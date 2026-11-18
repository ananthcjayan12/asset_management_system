from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("assets/", include("apps.assets.urls")),
    path("movements/", include("apps.movements.urls")),
    path("gatepasses/", include("apps.gatepasses.urls")),
    path("disposal/", include("apps.disposal.urls")),
    path("imports/", include("apps.imports_app.urls")),
    path("reports/", include("apps.reporting.urls")),
    path("", include("apps.core.urls")),
]

def serve_public_media(request, path):
    root = Path(settings.MEDIA_ROOT).resolve()
    target = (root / path).resolve()
    if target.is_relative_to(root / "gatepass_attachments"):
        raise Http404
    return serve(request, path, document_root=root)


if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve_public_media),
    ]
