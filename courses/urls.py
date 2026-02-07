from django.urls import path
from . import views
from .views import teacher_add_question, teacher_create_course, teacher_courses,  teacher_delete_question,  teacher_lesson_quiz, teacher_quiz_questions, teacher_update_question, teacher_update_quiz

urlpatterns = [

    # =====================
    # API (JWT ONLY)
    # =====================
    path("courses/", views.course_list),
    path("courses/<int:course_id>/lessons/", views.course_lessons),
    path("enroll/<int:course_id>/", views.enroll, name="enroll"),

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
    path("teacher/create-course/", views.teacher_create_course),
    path("teacher/my-courses/", views.teacher_courses),

    
    path(
    "teacher/course/<int:course_id>/add-lesson/",
    views.teacher_add_lesson_by_course
    ),
    
    path("teacher/lesson/<int:lesson_id>/",views.teacher_lesson_detail),
    path("teacher/lesson/<int:lesson_id>/delete/", views.teacher_delete_lesson),
    path("teacher/quizzes/", views.teacher_quizzes),
    
    path(
    "teacher/quiz/<int:quiz_id>/questions/",
    views.teacher_quiz_questions
    ),
    path(
    "teacher/question/<int:question_id>/delete/",
    views.teacher_delete_question
    ),
    
    path(
    "teacher/lesson/<int:lesson_id>/quiz/",
    views.teacher_lesson_quiz
    ),
    path("teacher/quiz/<int:quiz_id>/question/", views.teacher_add_question),
    path(
    "teacher/question/<int:question_id>/update/",
    views.teacher_update_question
    ),
    path(
    "teacher/quiz/<int:quiz_id>/update/",
    views.teacher_update_quiz
    ),
    path(
    "teacher/course/<int:course_id>/update/",
    views.teacher_update_course
    ),
    path("teacher/students/", views.teacher_students),
    path("courses/", views.admin_courses),
]