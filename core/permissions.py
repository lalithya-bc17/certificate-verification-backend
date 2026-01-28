from rest_framework.permissions import BasePermission
from .models import Student, Teacher


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return hasattr(request.user, 'student')

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return Teacher.objects.filter(user=request.user).exists()