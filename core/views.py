from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Student, Teacher
from .serializers import StudentSerializer, TeacherSerializer
from .permissions import IsStudent, IsTeacher
from rest_framework.permissions import IsAdminUser

from django.contrib.auth.models import User
from rest_framework import status
from django.db import IntegrityError


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent])
def students_list(request):
    students = Student.objects.all()
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def teachers_list(request):
    teachers = Teacher.objects.all()
    serializer = TeacherSerializer(teachers, many=True)
    return Response(serializer.data)


from rest_framework.permissions import AllowAny

from courses.models import Certificate, Course, Enrollment

from django.db import transaction

@api_view(["POST"])
@permission_classes([AllowAny])
def student_signup(request):
    data = request.data

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            student = user.student
            default_course = Course.objects.first()
            if default_course:
                Enrollment.objects.get_or_create(
                    student=student,
                    course=default_course
                )

        return Response(
            {"message": "Student account created & enrolled"},
            status=status.HTTP_201_CREATED
        )

    except IntegrityError:
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from core.models import Student, Teacher


class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        # 🔍 Detect role
        if user.is_superuser or user.is_staff:
            role = "admin"
        elif hasattr(user, "teacher"):
            role = "teacher"
        elif hasattr(user, "student"):
            role = "student"
        else:
            role = "unknown"

        # ✅ Attach role to response
        data["role"] = role
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    return Response({
        "total_users": User.objects.count(),
        "total_students": Student.objects.count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "total_certificates": Certificate.objects.count(),
    })

from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_users(request):
    users = User.objects.all()
    return Response([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
        }
        for u in users
    ])