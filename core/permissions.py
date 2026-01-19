from rest_framework.permissions import BasePermission
from .models import Student, Teacher

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return Student.objects.filter(user=request.user).exists()

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return Teacher.objects.filter(user=request.user).exists()