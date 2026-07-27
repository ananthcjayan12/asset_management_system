from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
