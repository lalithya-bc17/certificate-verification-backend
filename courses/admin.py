from django.contrib import admin
from .models import Course, Lesson, Enrollment, Progress, Quiz, Question, StudentAnswer
from .models import Certificate



@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["id", "title"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "course", "order"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "course"]


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "lesson", "completed"]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "lesson"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "quiz", "correct"]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "question", "selected", "is_correct"]
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "course", "issued_at"]
    list_filter = ('is_revoked', 'issued_at')
    search_fields = ('student__username', 'course__title')
