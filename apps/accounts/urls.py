from django.contrib.auth import views as auth_views
from django.urls import path
app_name = "accounts"
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-change/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change.html", success_url="/"), name="password_change"),
]
