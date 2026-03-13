from datetime import datetime
from django.utils import timezone
from planner.models import IntegrityLog


def get_threshold_percentage(priority_score):
    """
    Map priority score to adaptive threshold percentage.
    """

    if priority_score < 3.5:
        return 0.35
    elif priority_score < 5:
        return 0.45
    elif priority_score < 6.5:
        return 0.55
    else:
        return 0.65


def can_complete(studyplan):
    """
    Validate whether a study plan can be marked complete.
    Returns structured response.
    """

    now = timezone.now()
    generation_time = studyplan.generation_timestamp

    elapsed_seconds = (now - generation_time).total_seconds()
    elapsed_hours = elapsed_seconds / 3600

    threshold_percentage = get_threshold_percentage(studyplan.priority_score)

    required_hours = studyplan.allocated_hours * threshold_percentage

    if elapsed_hours < required_hours:

        return {
            "allowed": False,
            "reason": "threshold_not_met",
            "required_hours": round(required_hours, 2),
            "elapsed_hours": round(elapsed_hours, 2),
            "threshold_percentage": threshold_percentage
        }

    # Suspicious detection (barely above threshold)
    suspicious = False
    if elapsed_hours < (studyplan.allocated_hours * (threshold_percentage + 0.05)):
        suspicious = True

        IntegrityLog.objects.create(
            user=studyplan.user,
            studyplan=studyplan,
            allocated_hours=studyplan.allocated_hours,
            elapsed_time=round(elapsed_hours, 2),
            required_threshold=round(required_hours, 2)
        )

    return {
        "allowed": True,
        "suspicious": suspicious,
        "elapsed_hours": round(elapsed_hours, 2),
        "required_hours": round(required_hours, 2),
        "threshold_percentage": threshold_percentage
    }