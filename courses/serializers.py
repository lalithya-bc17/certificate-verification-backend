from rest_framework import serializers
from .models import Course, Lesson, Enrollment, Progress


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    quiz_id = serializers.IntegerField(source="quiz.id", read_only=True)
    has_quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id", "title", "order", "video", "content",
            "quiz_id", "has_quiz"
        ]

    def get_has_quiz(self, obj):
        return hasattr(obj, "quiz") and obj.quiz is not None


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"


class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = "__all__"