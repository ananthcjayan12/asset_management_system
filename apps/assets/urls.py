from django.urls import path
from . import views
app_name = "assets"
urlpatterns = [
    path("", views.asset_list, name="list"),
    path("new/", views.asset_create, name="create"),
    path("<int:pk>/", views.asset_detail, name="detail"),
    path("<int:pk>/edit/", views.asset_update, name="update"),
    path("<int:pk>/qr.png", views.qr_image, name="qr_image"),
    path("q/<uuid:token>/", views.qr_page, name="qr_page"),
    path("summary/", views.asset_summary, name="summary"),
    path("verification/", views.verification_list, name="verification_list"),
    path("verification/record/", views.verification_record, name="verification_record"),
]
