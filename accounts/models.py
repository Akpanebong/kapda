from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "System administrator"
        TEACHER = "teacher", "Education officer"
        DATA_ENTRY = "data_entry", "Data entry officer"
        MEAL = "meal", "M&E / MEAL officer"
        MANAGER = "manager", "Programme manager"
        VIEWER = "viewer", "Read-only viewer"
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, unique=True, null=True, blank=True)
    reg_no = models.CharField(max_length=40, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DATA_ENTRY)
    job_title = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    projects = models.ManyToManyField("projects.Project", blank=True, related_name="assigned_users")
    must_change_password = models.BooleanField(default=True)

    def __str__(self):
        return self.get_full_name() or self.username
