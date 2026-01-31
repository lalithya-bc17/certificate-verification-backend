from django.urls import path
from . import views

urlpatterns = [

    # =====================
    # API (JWT ONLY)
    # =====================
    path("courses/", views.course_list),
    path("courses/<int:course_id>/lessons/", views.course_lessons),
    path("enroll/", views.enroll),

    path("student/dashboard/", views.student_dashboard),
    path("student/continue/", views.resume_learning),
    path("student/course/<int:course_id>/resume/", views.resume_course),
    

    path("student/lesson/<int:lesson_id>/", views.lesson_detail),
    path("student/lesson/<int:lesson_id>/can-access/", views.can_access_lesson),
    path("student/lesson/<int:lesson_id>/complete/", views.mark_lesson_completed),

    path("courses/<int:course_id>/progress/", views.course_progress),
    path("student/quiz/<int:quiz_id>/submit/", views.submit_quiz),
    path("quiz/<int:quiz_id>/", views.quiz_detail),

    path("certificate/<int:course_id>/", views.certificate),
    path("verify-certificate/<uuid:id>/", views.verify_certificate),

    # 🔔 Notifications (JWT)
    path("notifications/", views.notifications_api),
    path("notifications/<int:id>/read/", views.mark_notification_read_api),
    path("notifications/unread-count/", views.unread_notification_count_api),
    path("teacher/add-lesson/", views.teacher_add_lesson),
    path("teacher/quizzes/", views.teacher_quizzes),
    path("teacher/students/", views.teacher_students),
]