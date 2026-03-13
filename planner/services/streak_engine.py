from datetime import date, timedelta
from planner.models import StudyPlan


def is_day_productive(user, target_date):
    """
    Returns True if at least one StudyPlan entry completed for that day.
    """
    return StudyPlan.objects.filter(
        user=user,
        date=target_date,
        completed=True
    ).exists()


def has_studyplan_entries(user, target_date):
    """
    Returns True if StudyPlan entries exist for that day.
    """
    return StudyPlan.objects.filter(
        user=user,
        date=target_date
    ).exists()


def update_streak(user):
    """
    Updates user's current and longest streak.
    """

    today = date.today()
    profile = user.userprofile

    # Check if today is productive
    if not is_day_productive(user, today):
        return {"status": "not_productive"}

    last_date = profile.last_productive_date

    # First productive day ever
    if last_date is None:
        profile.current_streak = 1
        profile.longest_streak = 1
        profile.last_productive_date = today
        profile.save()
        return {"status": "streak_started"}

    # Calculate gap
    delta_days = (today - last_date).days
    if delta_days == 0:
        return {"status": "already_counted"}

    if delta_days == 1:
        # Normal consecutive day
        profile.current_streak += 1

    elif delta_days > 1:
        # Check if intermediate days were neutral
        streak_broken = False

        for i in range(1, delta_days):
            check_date = last_date + timedelta(days=i)

            if has_studyplan_entries(user, check_date):
                # Had tasks but no completion → streak broken
                if not is_day_productive(user, check_date):
                    streak_broken = True
                    break

        if streak_broken:
            profile.current_streak = 1
        else:
            profile.current_streak += 1

    # Update longest streak
    if profile.current_streak > profile.longest_streak:
        profile.longest_streak = profile.current_streak

    profile.last_productive_date = today
    profile.save()

    return {
        "status": "streak_updated",
        "current_streak": profile.current_streak,
        "longest_streak": profile.longest_streak
    }