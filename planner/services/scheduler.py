from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction
from planner.models import Subject, StudyPlan

MIN_ALLOCATION = 0.5


def calculate_urgency(deadline):
    today = date.today()
    days_left = (deadline - today).days

    if days_left <= 0:
        return 5

    return 1 / days_left


def calculate_priority(subject):
    urgency = calculate_urgency(subject.deadline)
    return (subject.difficulty * 2) + urgency


def check_capacity(user, subject_data, daily_capacity):
    """
    Checks whether total required hours exceed available capacity.
    """
    today = date.today()
    max_deadline = max(item["subject"].deadline for item in subject_data)

    total_days = (max_deadline - today).days + 1
    total_capacity = total_days * daily_capacity

    total_required = sum(item["remaining_hours"] for item in subject_data)

    return {
        "total_required": total_required,
        "total_capacity": total_capacity,
        "overloaded": total_required > total_capacity
    }


def clear_future_incomplete_plans(user):
    """
    Delete only future incomplete study plans.
    Preserve completed entries.
    """
    today = date.today()

    StudyPlan.objects.filter(
        user=user,
        date__gte=today,
        completed=False
    ).delete()


def generate_plan(user, force_generate=False):
    """
    Production-grade weighted scheduler.
    """

    subjects = Subject.objects.filter(user=user, is_active=True)

    if not subjects.exists():
        return {"status": "no_subjects"}

    daily_capacity = user.userprofile.daily_study_hours
    today = date.today()

    subject_data = []

    for subject in subjects:
        remaining_topics = subject.total_topics - subject.completed_topics

        if remaining_topics <= 0:
            continue

        required_hours = remaining_topics
        priority = calculate_priority(subject)

        subject_data.append({
            "subject": subject,
            "remaining_hours": required_hours,
            "priority": priority
        })

    if not subject_data:
        return {"status": "nothing_to_plan"}

    capacity_info = check_capacity(user, subject_data, daily_capacity)

    if capacity_info["overloaded"]:
        scale_factor = capacity_info["total_capacity"] / capacity_info["total_required"]
        for item in subject_data:
            item["remaining_hours"] *= scale_factor

    total_priority = sum(item["priority"] for item in subject_data)

    if total_priority == 0:
        return {"status": "invalid_priority"}

    max_deadline = max(item["subject"].deadline for item in subject_data)

    current_date = today

    with transaction.atomic():

        clear_future_incomplete_plans(user)

        while current_date <= max_deadline:

            daily_allocated = 0

            for item in subject_data:

                if item["remaining_hours"] <= 0:
                    continue

                allocation_ratio = item["priority"] / total_priority
                allocated_hours = allocation_ratio * daily_capacity

                if allocated_hours < MIN_ALLOCATION:
                    allocated_hours = MIN_ALLOCATION

                remaining_daily_capacity = daily_capacity - daily_allocated
                allocated_hours = min(allocated_hours, remaining_daily_capacity)
                allocated_hours = min(allocated_hours, item["remaining_hours"])

                if allocated_hours <= 0:
                    continue

                StudyPlan.objects.create(
                    user=user,
                    subject=item["subject"],
                    date=current_date,
                    allocated_hours=round(allocated_hours, 2),
                    priority_score=item["priority"],
                    generation_timestamp=timezone.now()
                )

                item["remaining_hours"] -= allocated_hours
                daily_allocated += allocated_hours

            current_date += timedelta(days=1)

    return {"status": "plan_generated"}