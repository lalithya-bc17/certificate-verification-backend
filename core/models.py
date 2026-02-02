from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # OPTIONAL profile fields (NOT required at signup)
    roll_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # SYSTEM FIELD (auto-managed)
    completed_quizzes = models.ManyToManyField(
        "courses.Quiz",
        blank=True
    )

    def __str__(self):
        return self.user.username


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username