from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenView, admin_stats, admin_users, bootstrap_admin


urlpatterns = [
    # Lists (protected)
    path("students/", views.students_list),
    path("teachers/", views.teachers_list),
    
    # Student signup (PUBLIC)
    path("signup/student/", views.student_signup, name="student-signup"),

    # ✅ JWT LOGIN WITH ROLE
    path("token/", views.CustomTokenView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/admin/stats/", admin_stats),
    path("api/admin/users/", admin_users),
    path("api/bootstrap-admin/", bootstrap_admin),
]