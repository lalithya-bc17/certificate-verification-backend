from rest_framework import serializers
from .models import Student, Teacher


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = "__all__"
    
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if hasattr(user, "student"):
            data["role"] = "student"
        elif hasattr(user, "teacher"):
            data["role"] = "teacher"
        elif user.is_staff or user.is_superuser:
            data["role"] = "admin"
        else:
            data["role"] = "student"

        return data