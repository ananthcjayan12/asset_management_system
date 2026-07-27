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
]
