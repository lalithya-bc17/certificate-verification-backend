from django.db import models
from core.models import Student, Teacher
import uuid


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField(default=1)
    video = models.FileField(upload_to="lesson_videos/", blank=True, null=True)
    # One quiz per lesson
    quiz = models.OneToOneField("Quiz", on_delete=models.SET_NULL, null=True, blank=True, related_name="lesson")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Quiz(models.Model):
    # ❌ Remove OneToOneField to Course
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=255)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct= models.CharField(
        max_length=1,
        choices=[('A','A'), ('B','B'), ('C','C'), ('D','D')]
    )  # 'A', 'B', 'C', 'D'

    def __str__(self):
        return self.text


class StudentAnswer(models.Model):
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected = models.CharField(max_length=1)
    is_correct = models.BooleanField()


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["student", "course"]

        def __str__(self):
            return f"{self.student} enrolled in {self.course}"

class Progress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ["student", "lesson"]

        def __str__(self):
            return f"{self.student} - {self.lesson} : {'Completed' if self.completed else 'Incomplete'}"

from django.db import models
from django.contrib.auth.models import User
from courses.models import Course  # adjust if needed

class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)  # 🔒 SECURITY FLAG
    class Meta:
        unique_together = ("student", "course")
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"