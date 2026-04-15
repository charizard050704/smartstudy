from django.urls import path
from . import views
from django.urls import reverse_lazy

urlpatterns = [
    path("", views.dashboard),
    path("generate-plan/", views.generate_plan_view, name="generate_plan"),
    path("complete/<int:plan_id>/", views.complete_plan_view, name="complete_plan"),
    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("leaderboard/api/", views.leaderboard_api, name="leaderboard_api"),
    path("tutorial-complete/", views.tutorial_complete, name="tutorial_complete"),
    path("forest/", views.forest_view, name="forest"),
    path("forest/index/", views.tree_index, name="tree_index"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
]