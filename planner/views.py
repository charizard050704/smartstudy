from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .models import StudyPlan
from planner.services.scheduler import generate_plan
from planner.services.completion_engine import complete_studyplan
from planner.services.leaderboard_engine import get_top_and_rank
from planner.models import ForestTree
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from datetime import datetime

def register_view(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            print("USER CREATED:", user.username)   # 🔥 DEBUG
            return redirect("/login/")

        else:
            print("FORM ERRORS:", form.errors)      # 🔥 VERY IMPORTANT

    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {
        "form": form
    })

def login_view(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/dashboard/")   # 🔥 FORCE REDIRECT

        else:
            return render(request, "login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "login.html")

@login_required
def dashboard(request):
    plans = StudyPlan.objects.filter(user=request.user).order_by("date")

    return render(request, "planner/dashboard.html", {
        "plans": plans
    })


@login_required
def generate_plan_view(request):

    if request.method == "POST":

        subject_name = request.POST.get("subject")
        difficulty = request.POST.get("difficulty")
        exam_date = request.POST.get("exam_date")

        if not subject_name or not difficulty or not exam_date:
            return JsonResponse({"status": "invalid_input"}, status=400)

        # Convert difficulty
        difficulty_map = {
            "easy": 1,
            "medium": 2,
            "hard": 3
        }

        difficulty_value = difficulty_map.get(difficulty, 2)

        # Convert date
        deadline = datetime.strptime(exam_date, "%Y-%m-%d").date()

        # ✅ CREATE SUBJECT
        subject, created = Subject.objects.get_or_create(
            user=request.user,
            name=subject_name,
            defaults={
                "difficulty": difficulty_value,
                "deadline": deadline,
                "total_topics": 10,
                "completed_topics": 0,
                "is_active": True
            }
        )

        # If already exists → update it
        if not created:
            subject.difficulty = difficulty_value
            subject.deadline = deadline
            subject.is_active = True
            subject.save()

        # ✅ NOW RUN SCHEDULER
        result = generate_plan(request.user)

        return JsonResponse(result)

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def complete_plan_view(request, plan_id):
    plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
    result = complete_studyplan(plan)
    return JsonResponse(result)

@login_required
def leaderboard_page(request):
    return render(request, "planner/leaderboard.html")

@login_required
def leaderboard_api(request):

    metric = request.GET.get("metric", "study_time")
    mode = request.GET.get("mode", "all_time")

    data = get_top_and_rank(
        current_user=request.user,
        metric=metric,
        mode=mode
    )
    data["current_user"] = request.user.username
    return JsonResponse(data)

@login_required
def tutorial_complete(request):
    if request.method == "POST":
        profile = request.user.userprofile
        profile.has_completed_tutorial = True
        profile.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "invalid"}, status=400)

@login_required
def forest_view(request):

    trees = ForestTree.objects.filter(user=request.user)

    tree_data = []

    for t in trees:
        tree_data.append({
            "species": t.species,
            "pos_x": t.pos_x,
            "pos_y": t.pos_y,
            "growth": t.growth_stage
        })

    return render(request, "planner/forest.html", {
        "trees": trees,
        "tree_json": json.dumps(tree_data)
    })

TREE_SPECIES = {
    "healthy": ["oak", "maple", "neem", "pine"],
    "rare": ["cherry_blossom", "jacaranda", "silver_birch"],
    "epic": ["redwood", "baobab", "dragon_tree"],
    "legendary": ["giant_sequoia", "methuselah_pine", "rainbow_eucalyptus"],
    "mythic": ["yggdrasil", "kalpavriksha", "world_tree"]
}

@login_required
def tree_index(request):

    user = request.user

    discovered = set(
        ForestTree.objects.filter(user=user)
        .values_list("species", flat=True)
    )

    collection = {}

    for tier, species_list in TREE_SPECIES.items():

        tier_data = []

        for s in species_list:

            tier_data.append({
                "name": s,
                "owned": s in discovered
            })

        collection[tier] = tier_data

    return render(request, "planner/tree_index.html", {
        "collection": collection
    })
    