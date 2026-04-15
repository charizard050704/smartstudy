from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # logout can stay OR we move it later
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("", include("planner.urls")),
]