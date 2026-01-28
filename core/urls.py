from django.urls import path
from . import views

urlpatterns = [
    # Lists (protected)
    path("students/", views.students_list),
    path("teachers/", views.teachers_list),

    # Student signup (PUBLIC)
    path("signup/student/", views.student_signup, name="student-signup"),

    # ✅ JWT LOGIN WITH ROLE
    path("token/", views.CustomTokenView.as_view(), name="token"),
]