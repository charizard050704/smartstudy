from django.utils import timezone
from django.db import transaction
from planner.services.integrity_engine import can_complete
from planner.services.streak_engine import update_streak
from planner.services.forest_engine import plant_tree
from planner.services.rewards_engine import check_and_update_mythic


def calculate_points(studyplan):
    """
    Hybrid scoring formula.
    """
    base = studyplan.allocated_hours * 10
    difficulty_bonus = studyplan.priority_score * 5
    return int(base + difficulty_bonus)


@transaction.atomic
def complete_studyplan(studyplan):
    """
    Master completion handler.
    """

    if studyplan.completed:
        return {"status": "already_completed"}

    integrity_result = can_complete(studyplan)

    if not integrity_result["allowed"]:
        return {
            "status": "blocked",
            "reason": integrity_result["reason"],
            "required_hours": integrity_result["required_hours"],
            "elapsed_hours": integrity_result["elapsed_hours"],
        }

    # Mark as completed
    studyplan.completed = True
    studyplan.completed_hours = studyplan.allocated_hours
    studyplan.completion_timestamp = timezone.now()
    studyplan.save()

    # Award points
    points = calculate_points(studyplan)
    profile = studyplan.user.userprofile
    profile.total_points += points
    profile.save()

    # ✅ IMPORTANT: Update streak FIRST
    streak_result = update_streak(studyplan.user)

    # Then plant tree
    forest_result = plant_tree(studyplan.user)

    # Then mythic update
    mythic_result = check_and_update_mythic(studyplan.user)

    return {
        "status": "completed",
        "points_awarded": points,
        "streak": streak_result,
        "forest": forest_result,
        "mythic": mythic_result
    }