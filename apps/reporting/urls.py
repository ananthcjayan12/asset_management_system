from django.urls import path
from . import views
app_name = "reporting"
urlpatterns = [path("", views.dashboard, name="dashboard"), path("assets/", views.asset_report, name="asset_report"), path("assets.csv", views.assets_csv, name="assets_csv")]
