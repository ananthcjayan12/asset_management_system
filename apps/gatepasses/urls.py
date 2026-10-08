from django.urls import path
from . import views
app_name = "gatepasses"
urlpatterns = [
    path("", views.gatepass_list, name="list"), path("new/", views.gatepass_create, name="create"),
    path("<int:pk>/", views.gatepass_detail, name="detail"), path("<int:pk>/division-approve/", views.division_approve, name="division_approve"),
    path("<int:pk>/approve/", views.approve, name="approve"), path("<int:pk>/reject/", views.reject, name="reject"),
    path("<int:pk>/outward/", views.outward, name="outward"), path("<int:pk>/inward/", views.inward, name="inward"),
]
