from django.urls import path
from . import views
app_name = "imports_app"
urlpatterns = [path("", views.batch_list, name="list"), path("upload/", views.upload, name="upload"), path("<int:pk>/", views.detail, name="detail"), path("<int:pk>/confirm/", views.confirm, name="confirm")]
