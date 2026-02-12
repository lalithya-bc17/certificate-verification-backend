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
from django.contrib.auth.models import User
from courses.models import Course, Enrollment, Certificate
from core.models import Student, Teacher
from courses.models import Announcement


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

            # student profile is created automatically
            # ❌ NO auto enrollment here

        return Response(
            {"message": "Student account created"},
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
        "total_teachers": Teacher.objects.count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "total_certificates": Certificate.objects.count(),
        "total_announcements": Announcement.objects.count(),

    })

from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from django.db.models import Q

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_users(request):
    search = request.GET.get("search", "")

    users = User.objects.all()

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )

    data = []

    for u in users:
        if u.is_staff:
            role = "Admin"
        elif hasattr(u, "teacher"):
            role = "Teacher"
        elif hasattr(u, "student"):
            role = "Student"
        else:
            role = "User"

        data.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": role,
        })

    return Response(data)



@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_enrollments(request):
    enrollments = Enrollment.objects.all()
    return Response([
        {
            "id": e.id,
            "student_name": e.student.user.username,
            "course_title": e.course.title,
            "enrolled_at": e.joined_at,
        }
        for e in enrollments
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_certificates(request):
    certificates = Certificate.objects.all()
    return Response([
        {
            "id": c.id,
            "student_name": c.student.username,
            "course_title": c.course.title,
            "issued_at": c.issued_at,
            "is_revoked": c.is_revoked,

        }
        for c in certificates
    ])

from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["POST"])
@permission_classes([AllowAny])
def bootstrap_admin(request):
    if User.objects.filter(is_superuser=True).exists():
        return Response({"detail": "Admin already exists"}, status=400)

    User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@example.com"
    )

    return Response({"detail": "Admin created successfully"})