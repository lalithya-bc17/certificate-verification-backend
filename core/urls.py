from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenView, admin_stats, admin_users, bootstrap_admin
from .views import admin_enrollments, admin_certificates


urlpatterns = [
    # Lists (protected)
    path("students/", views.students_list),
    path("teachers/", views.teachers_list),
    
    # Student signup (PUBLIC)
    path("signup/student/", views.student_signup, name="student-signup"),

    # ✅ JWT LOGIN WITH ROLE
    path("token/", views.CustomTokenView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/stats/", views.admin_stats),
    path("admin/users/", views.admin_users),
    path("admin/enrollments/", views.admin_enrollments),
    path("admin/certificates/", views.admin_certificates),
    path("api/bootstrap-admin/", bootstrap_admin),
]