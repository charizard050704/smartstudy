from datetime import date, timedelta
from django.db.models import Sum
from django.contrib.auth.models import User
from planner.models import StudyPlan

# --------------------------------------------------
# DATE RANGE HANDLING (ONLY FOR TIME-BASED METRICS)
# --------------------------------------------------

def get_date_range(mode):
    today = date.today()

    if mode == "daily":
        return today, today

    elif mode == "weekly":
        start = today - timedelta(days=today.weekday())
        return start, today

    elif mode == "monthly":
        start = today.replace(day=1)
        return start, today

    elif mode == "all_time":
        return None, None

    else:
        raise ValueError("Invalid mode")


# --------------------------------------------------
# STUDY TIME CALCULATION
# --------------------------------------------------

def get_study_time(user, mode):
    start, end = get_date_range(mode)

    qs = StudyPlan.objects.filter(user=user, completed=True)

    if start and end:
        qs = qs.filter(date__range=(start, end))

    result = qs.aggregate(total=Sum("completed_hours"))
    return result["total"] or 0


# --------------------------------------------------
# POINTS CALCULATION (DYNAMIC)
# --------------------------------------------------

def get_points(user, mode):
    start, end = get_date_range(mode)

    qs = StudyPlan.objects.filter(user=user, completed=True)

    if start and end:
        qs = qs.filter(date__range=(start, end))

    total_points = 0
    for sp in qs:
        total_points += int(round((sp.allocated_hours * 10) + (sp.priority_score * 5)))

    return total_points


# --------------------------------------------------
# MAIN LEADERBOARD BUILDER
# --------------------------------------------------

def build_leaderboard(metric="study_time", mode="all_time"):

    users = User.objects.all()
    leaderboard_data = []

    MODES = ["daily", "weekly", "monthly", "all_time"]

    for user in users:
        profile = user.userprofile

        metrics = {
            "current_streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
        }

        # Precompute metric families
        for m in MODES:
            metrics[f"points_{m}"] = get_points(user, m)
            metrics[f"study_time_{m}"] = get_study_time(user, m)

        leaderboard_data.append({
            "username": user.username,
            "metrics": metrics
        })

    def ranking_key(entry):
        m = entry["metrics"]
        key = []

        # ---------- PRIMARY ----------
        if metric in ["points", "study_time"]:
            key.append(-m[f"{metric}_{mode}"])
        else:
            key.append(-m[metric])

        # ---------- STREAK PAIR ----------
        if metric == "current_streak":
            key.append(-m["longest_streak"])

        elif metric == "longest_streak":
            key.append(-m["current_streak"])

        else:
            key.append(-m["current_streak"])
            key.append(-m["longest_streak"])

        # ---------- OPPOSITE FAMILY CASCADE ----------
        if metric == "points":
            for md in MODES:
                key.append(-m[f"study_time_{md}"])

        elif metric == "study_time":
            for md in MODES:
                key.append(-m[f"points_{md}"])

        else:  # streak case
            for md in MODES:
                key.append(-m[f"points_{md}"])
            for md in MODES:
                key.append(-m[f"study_time_{md}"])

        # ---------- SAME FAMILY OTHER MODES ----------
        if metric in ["points", "study_time"]:
            for md in MODES:
                if md != mode:
                    key.append(-m[f"{metric}_{md}"])

        # ---------- USERNAME ----------
        key.append(entry["username"])

        return tuple(key)

    leaderboard_data.sort(key=ranking_key)

    formatted = []

    for entry in leaderboard_data:
        m = entry["metrics"]

        if metric in ["points", "study_time"]:
            value = m[f"{metric}_{mode}"]
        else:
            value = m[metric]

        formatted.append({
            "username": entry["username"],
            "value": value,
            "current_streak": m["current_streak"],
            "longest_streak": m["longest_streak"],
            "study_time_all": m["study_time_all_time"]
        })

    return formatted


# --------------------------------------------------
# TOP 10 + USER RANK
# --------------------------------------------------

def get_top_and_rank(current_user, metric="study_time", mode="all_time"):

    data = build_leaderboard(metric, mode)

    top_10 = data[:10]

    user_rank = None
    user_data = None

    for index, entry in enumerate(data):
        if entry["username"] == current_user.username:
            user_rank = index + 1
            user_data = entry
            break

    return {
        "top_10": top_10,
        "your_rank": user_rank,
        "your_data": user_data
    }