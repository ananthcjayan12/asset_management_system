from django.urls import path
from . import views
app_name = "movements"
urlpatterns = [path("", views.movement_list, name="list"), path("transfer/", views.transfer, name="transfer"), path("return/", views.return_to_stock, name="return")]
