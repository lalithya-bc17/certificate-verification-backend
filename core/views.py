from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Student, Teacher
from .serializers import StudentSerializer, TeacherSerializer
from .permissions import IsStudent, IsTeacher


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