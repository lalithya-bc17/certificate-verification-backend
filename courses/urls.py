from django.urls import path
from . import views

urlpatterns = [

    # -------------------
    # API ROUTES
    # -------------------
    path("courses/", views.course_list),
    path("courses/<int:course_id>/lessons/", views.course_lessons),
    path("enroll/", views.enroll),

    path("student/lesson/<int:lesson_id>/", views.lesson_detail),
    path("student/lesson/<int:lesson_id>/can-access/", views.can_access_lesson),

    path("student/dashboard/", views.student_dashboard),
    path("student/continue/", views.resume_learning),

    path("courses/<int:course_id>/progress/", views.course_progress),
    path("student/quiz/<int:quiz_id>/submit/", views.submit_quiz),

    # -------------------
    # HTML UI
    # -------------------
    path("dashboard/", views.student_dashboard_page, name="student-dashboard"),
    path("student/course/<int:course_id>/resume/", views.resume_course),

    path("resume/<int:course_id>/", views.resume_course, name="resume_course"),
    path("certificate/<int:course_id>/", views.certificate, name="certificate"),

    path("student/lesson/<int:lesson_id>/complete/", views.mark_lesson_completed),
    path("quiz/<int:quiz_id>/", views.quiz_detail),

    path("verify-certificate/<uuid:id>/", views.verify_certificate, name="verify_certificate"),

    # ✅ Lesson page (VIDEO PAGE)
    path(
    "lesson/<int:lesson_id>/",
    views.lesson_detail_page,
    name="lesson-detail"
),
    path("announcements/", views.announcements_page, name="announcements"),
    path("notifications/", views.notifications_page, name="notifications"),
]