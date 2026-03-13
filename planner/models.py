from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


# ----------------------------
# USER PROFILE
# ----------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    daily_study_hours = models.FloatField(default=2.0, validators=[MinValueValidator(0.5)])

    total_points = models.IntegerField(default=0)

    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_productive_date = models.DateField(null=True, blank=True)
    
    has_completed_tutorial = models.BooleanField(default=False)

    save_epic = models.BooleanField(default=True)
    save_legendary = models.BooleanField(default=True)

    selected_theme = models.CharField(max_length=50, default="default")
    selected_tree_type = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["total_points"]),
            models.Index(fields=["current_streak"]),
            models.Index(fields=["longest_streak"]),
        ]

    def __str__(self):
        return f"{self.user.username} Profile"


# ----------------------------
# SUBJECT
# ----------------------------

class Subject(models.Model):
    DIFFICULTY_CHOICES = [
        (1, "Easy"),
        (2, "Medium"),
        (3, "Hard"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    deadline = models.DateField()

    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)

    total_topics = models.IntegerField(validators=[MinValueValidator(1)])
    completed_topics = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["deadline"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# ----------------------------
# STUDY PLAN
# ----------------------------

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    date = models.DateField()

    allocated_hours = models.FloatField(validators=[MinValueValidator(0.1)])
    completed_hours = models.FloatField(default=0)

    completed = models.BooleanField(default=False)

    generation_timestamp = models.DateTimeField(default=timezone.now)
    completion_timestamp = models.DateTimeField(null=True, blank=True)

    priority_score = models.FloatField(default=0)

    integrity_flag = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "completed"]),
            models.Index(fields=["user", "date", "subject"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.subject.name} - {self.date}"


# ----------------------------
# FOREST TREE
# ----------------------------

class ForestTree(models.Model):
    TREE_STATUS_CHOICES = [
        ("healthy", "Healthy"),
        ("rare", "Rare"),
        ("epic", "Epic"),
        ("legendary", "Legendary"),
        ("mythic", "Mythic"),
        ("dry", "Dry"),
        ("cut", "Cut"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    planted_date = models.DateField(default=timezone.now)

    status = models.CharField(max_length=20, choices=TREE_STATUS_CHOICES)
    
    species = models.CharField(max_length=50, default="oak")

    tree_type = models.CharField(max_length=50, default="default")

    pos_x = models.FloatField()
    pos_y = models.FloatField()

    depth_layer = models.IntegerField()  # 1=front, 2=mid, 3=back

    growth_stage = models.IntegerField(default=0)  # 0–3

    is_protected = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["depth_layer"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.status} Tree"


# ----------------------------
# INVENTORY SYSTEM
# ----------------------------

class UserInventoryTree(models.Model):
    TREE_TYPE_CHOICES = [
        ("rare", "Rare"),
        ("epic", "Epic"),
        ("legendary", "Legendary"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    tree_type = models.CharField(max_length=20, choices=TREE_TYPE_CHOICES)

    quantity = models.IntegerField(default=0)
    total_earned = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "tree_type")

    def __str__(self):
        return f"{self.user.username} - {self.tree_type} x{self.quantity}"


# ----------------------------
# INTEGRITY LOG
# ----------------------------

class IntegrityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    studyplan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE)

    allocated_hours = models.FloatField()
    elapsed_time = models.FloatField()
    required_threshold = models.FloatField()

    flagged_at = models.DateTimeField(auto_now_add=True)

    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Integrity Flag - {self.user.username}"