from django.conf import settings
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

if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
