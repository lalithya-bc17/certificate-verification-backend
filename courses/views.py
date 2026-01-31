from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Student
from core.permissions import IsStudent, IsTeacher
from .models import Certificate
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.http import JsonResponse



from .models import (
    Course, Lesson, Enrollment, Progress,
    Quiz, Question, StudentAnswer, Announcement
)
from .serializers import CourseSerializer, LessonSerializer


# -----------------------------
# COURSES & ENROLLMENT
# -----------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_list(request):
    courses = Course.objects.all()
    return Response(CourseSerializer(courses, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def course_lessons(request, course_id):
    student = request.user.student
    lessons = Lesson.objects.filter(course_id=course_id).order_by("order")

    data = []
    for l in lessons:
        unlocked = is_lesson_unlocked(student, l)
        completed = Progress.objects.filter(student=student, lesson=l, completed=True).exists()
        status = "completed" if completed else "incomplete"
        
        data.append({
            "id": l.id,
            "title": l.title,
            "order": l.order,
            "unlocked": unlocked,
            "status": status,   
        })

    return Response({
        "courses":data
        })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def enroll(request):
    course_id = request.data.get("course")
    student = request.user.student
    Enrollment.objects.get_or_create(student=student, course_id=course_id)
    return Response({"message": "Enrolled"})


# -----------------------------
# LESSON LOCKING LOGIC
# -----------------------------

def is_lesson_unlocked(student, lesson):
    """
    First lesson is always unlocked.
    Other lessons require all previous lessons AND their quizzes (if any)
    to be completed.
    """

    if lesson.order == 1:
        return True

    previous_lessons = Lesson.objects.filter(
        course=lesson.course,
        order__lt=lesson.order
    ).order_by("order")

    for prev in previous_lessons:
        # Lesson must be completed
        lesson_done = Progress.objects.filter(
            student=student,
            lesson=prev,
            completed=True
        ).exists()

        # Quiz check (SAFE)
        try:
            quiz = prev.quiz
            quiz_done = student.completed_quizzes.filter(id=quiz.id).exists()
        except Quiz.DoesNotExist:
            quiz_done = True  # no quiz → OK

        if not (lesson_done and quiz_done):
            return False

    return True


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def lesson_detail(request, lesson_id):
    student = request.user.student
    lesson = get_object_or_404(Lesson, id=lesson_id)

    already_done = Progress.objects.filter(
        student=student,
        lesson=lesson,
        completed=True
    ).exists()

    if not already_done and not is_lesson_unlocked(student, lesson):
        return Response({"detail": "Lesson locked"}, status=403)

    return Response({
        "id": lesson.id,
        "title": lesson.title,
        "content": lesson.content,
        "video_url": lesson.video_url,
        "quiz_id": lesson.quiz.id if hasattr(lesson, "quiz") and lesson.quiz else None,
    })

from django.contrib.auth.decorators import login_required


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = request.user.student
    lesson = get_object_or_404(Lesson, quiz=quiz)

    passed = student.completed_quizzes.filter(id=quiz.id).exists()

    return Response({
        "id": quiz.id,
        "title": quiz.title,
        "passed": passed,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "a": q.option_a,
                "b": q.option_b,
                "c": q.option_c,
                "d": q.option_d,
            }
            for q in quiz.questions.all()
        ]
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def can_access_lesson(request, lesson_id):
    student = request.user.student
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if not Enrollment.objects.filter(student=student, course=lesson.course).exists():
        return Response({"access": False})

    if lesson.order == 1:
        return Response({"access": True})

    prev = Lesson.objects.filter(
        course=lesson.course,
        order=lesson.order - 1
    ).first()

    done = Progress.objects.filter(
        student=student,
        lesson=prev,
        completed=True
    ).exists()

    return Response({"access": done})


# -----------------------------
# PROGRESS & DASHBOARD (API)
# -----------------------------

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    try:
        student = request.user.student
    except ObjectDoesNotExist:
        return Response(
            {"detail": "User is not a student"},
            status=status.HTTP_403_FORBIDDEN
        )

    enrollments = Enrollment.objects.filter(student=student)

    data = []

    for e in enrollments:
        lessons = Lesson.objects.filter(course=e.course)
        total = lessons.count()

        completed = Progress.objects.filter(
            student=student,
            lesson__course=e.course,
            completed=True
        ).count()

        percent = int((completed / total) * 100) if total else 0

        data.append({
            "course_id": e.course.id,
            "course": e.course.title,
            "total": total,
            "completed": completed,
            "progress": percent
        })

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def course_progress(request, course_id):
    student = request.user.student
    course = get_object_or_404(Course, id=course_id)

    total = Lesson.objects.filter(course=course).count()
    completed = Progress.objects.filter(
        student=student,
        lesson__course=course,
        completed=True
    ).count()

    percent = int((completed / total) * 100) if total else 0

    return Response({
        "course": course.title,
        "completed": completed,
        "total": total,
        "percentage": percent
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def resume_learning(request):
    student = request.user.student
    enrollments = Enrollment.objects.filter(student=student)

    response = []

    for e in enrollments:
        lessons = Lesson.objects.filter(course=e.course).order_by("order")

        completed = Progress.objects.filter(
            student=student,
            lesson__course=e.course,
            completed=True
        ).values_list("lesson_id", flat=True)

        last_done = None
        next_lesson = None

        for l in lessons:
            if l.id in completed:
                last_done = l
            else:
                next_lesson = l
                break

        response.append({
            "course": e.course.title,
            "last_completed": last_done.title if last_done else None,
            "continue_lesson": next_lesson.title if next_lesson else None
        })

    return Response(response)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def resume_course(request, course_id):
    student = request.user.student
    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=student, course=course
    ).first()

    if not enrollment:
        return Response(
            {"error": "Not enrolled in this course"},
            status=403
        )

    lessons = Lesson.objects.filter(course=course).order_by("order")

    if not lessons.exists():
        return Response(
            {"error": "No lessons found for this course"},
            status=404
        )

    for lesson in lessons:
        progress = Progress.objects.filter(
            student=student,
            lesson=lesson,
            completed=True
        ).first()

        if not progress:
            return Response({
                "lesson_id": lesson.id,
                "title": lesson.title,
                "order": lesson.order,
                "status": "resume"
            })

    last = lessons.last()
    return Response({
        "lesson_id": last.id,
        "title": last.title,
        "order": last.order,
        "status": "completed"
    })


# -----------------------------
# QUIZ SUBMIT & AUTO PROGRESS
# -----------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def submit_quiz(request, quiz_id):
    student = request.user.student
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = get_object_or_404(Lesson, quiz=quiz)

    answers = request.data.get("answers", {})
    total = quiz.questions.count()

    if not answers:
        return Response({"error": "No answers submitted"}, status=400)

    correct = 0
    result = []

    import re

    for q in quiz.questions.all():
        selected = str(answers.get(str(q.id), "")).strip().lower()
        correct_option = re.sub(r'[^a-z]', '', q.correct.strip().lower())
        is_correct = selected == correct_option

        if is_correct:
            correct += 1

        result.append({
            "question_id": q.id,
            "selected": selected,
            "correct": correct_option,
            "is_correct": is_correct
        })

        StudentAnswer.objects.update_or_create(
            student=student,
            question=q,
            defaults={"selected": selected, "is_correct": is_correct}
        )

    score = int((correct / total) * 100)
    passed = score >= 60

    next_lesson_id = None
    all_lessons_completed = False

    if passed:
        # mark lesson completed
        Progress.objects.update_or_create(
            student=student,
            lesson=lesson,
            defaults={"completed": True}
        )

        # mark quiz completed ✅
        student.completed_quizzes.add(quiz)

        # find next lesson
        next_lesson = Lesson.objects.filter(
            course=lesson.course,
            order__gt=lesson.order
        ).order_by("order").first()

        if not next_lesson:
            next_lesson = Lesson.objects.filter(
                course=lesson.course,
                id__gt=lesson.id
            ).order_by("id").first()

        if next_lesson:
            next_lesson_id = next_lesson.id
        else:
            all_lessons_completed = True

    return Response({
        "score": score,
        "passed": passed,
        "details": result,
        "next_lesson_id": next_lesson_id,
        "all_lessons_completed": all_lessons_completed
    })
# -----------------------------
# PHASE-4B — STUDENT DASHBOARD UI
# -----------------------------
# LEGACY - DO NOT USE FOR REACT
@login_required
def student_dashboard_page(request):
    student = request.user.student
    enrollments = Enrollment.objects.filter(student=student)

    dashboard = []

    for e in enrollments:
        lessons = Lesson.objects.filter(course=e.course).order_by("order")

        completed_ids = Progress.objects.filter(
            student=student,
            lesson__course=e.course,
            completed=True
        ).values_list("lesson_id", flat=True)

        total = lessons.count()
        completed = len(completed_ids)
        percent = int((completed / total) * 100) if total else 0
        print("PROGRESS:", percent)

        resume = None
        for l in lessons:
            if l.id not in completed_ids:
                resume = l
                break

        dashboard.append({
            "course": e.course,
            "lessons": lessons,
            "completed_ids": completed_ids,
            "completed": completed,
            "total": total,
            "progress": percent,
            "resume": resume
        })

    return render(request, "courses/student_dashboard.html", {
        "dashboard": dashboard
    })
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Course, Progress
from core.permissions import IsStudent  # if you have this
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils.timezone import now
import os
from django.conf import settings
import os
import base64
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from weasyprint import HTML

from .models import Course, Progress, Certificate
from django.conf import settings


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def certificate(request, course_id):
    user = request.user                  # ✅ User
    student = request.user.student       # ✅ Student profile

    course = get_object_or_404(Course, id=course_id)

    total = course.lessons.count()
    done = Progress.objects.filter(
        student=student,                 # Student model
        lesson__course=course,
        completed=True
    ).count()

    if done != total:
        return HttpResponse("You have not completed this course.", status=403)

    certificate_obj, created = Certificate.objects.get_or_create(
        student=user,                    # ✅ User model (matches Certificate)
        course=course,
    )
    if not certificate_obj.issued_at:
        certificate_obj.issued_at = now()
        certificate_obj.save()

    if created:
       Notification.objects.create(
        user=request.user,
        message="Your certificate has been generated ✅"
    )
    

    # 🚫 Block revoked certificates from downloading

    if certificate_obj.is_revoked:
        return HttpResponse("This certificate has been revoked.", status=403)

    RENDER_BASE_URL = "https://certificate-verification-backend-7gpb.onrender.com"

    verify_url = f"https://certificate-verification-backend-7gpb.onrender.com/verify-certificate/{certificate_obj.id}/" 
    print("VERIFY URL:", verify_url)
    

    qr = qrcode.make(verify_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    def file_path(path):
        return "file:///" + path.replace("\\", "/")

    logo_path = file_path(os.path.join(settings.BASE_DIR, "static", "brand", "logo.png"))
    people_icon = file_path(os.path.join(settings.BASE_DIR, "static", "brand", "people.png"))

    html_string = render_to_string(
        "courses/certificate_template.html",
        {
            "student_name": user.get_full_name() or user.username,
            "course_name": course.title,
            "date": now().strftime("%d %B %Y"),
            "logo_path": logo_path,
            "people_icon": people_icon,
            "qr_base64": qr_base64,
        }
    )

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{course.title}_certificate.pdf"'
    return response
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_lesson_completed(request, lesson_id):
    student = request.user.student
    lesson = Lesson.objects.get(id=lesson_id)

    progress, created = Progress.objects.get_or_create(student=student, lesson=lesson)
    if not progress.completed:
       progress.completed = True
       progress.save()

    Notification.objects.create(
        user=request.user,
        message="You have successfully completed a lesson 🎉"
    )
    return Response({"success": True})


from django.shortcuts import get_object_or_404, render
from .models import Certificate

from django.shortcuts import get_object_or_404, render

from django.shortcuts import render, get_object_or_404
from .models import Certificate
def verify_certificate(request, id):
    try:
        certificate = Certificate.objects.get(id=id)
    except Certificate.DoesNotExist:
        return render(request, "courses/verify_certificate.html", {
            "status": "invalid"
        })

    if certificate.is_revoked:
        return render(request, "courses/verify_certificate.html", {
            "status": "revoked",
            "certificate_id": certificate.id
        })
    

    return render(request, "courses/verify_certificate.html", {
        "status": "valid",
        "student": certificate.student.get_full_name() or certificate.student.username,
        "course": certificate.course.title,
        "issued_at": certificate.issued_at.strftime("%d %B %Y") if certificate.issued_at else "—",
        "certificate_id": certificate.id,
    })
from django.contrib.auth.decorators import login_required


from django.shortcuts import render, get_object_or_404
from .models import Lesson
# LEGACY - DO NOT USE FOR REACT
def lesson_detail_page(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, "courses/lesson_detail.html", {
        "lesson": lesson
    })
    # allow access if already completed

# LEGACY - DO NOT USE FOR REACT
def announcements_page(request):
    announcements = Announcement.objects.order_by('-created_at')
    return render(request, "courses/announcements.html", {
        "announcements": announcements
    })

from django.contrib.auth.decorators import login_required
from .models import Notification
# LEGACY - DO NOT USE FOR REACT

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Notification

# =========================
# 🔔 NOTIFICATIONS (JWT API)
# =========================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications_api(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return Response([
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(request, id):
    notification = get_object_or_404(
        Notification,
        id=id,
        user=request.user
    )
    notification.is_read = True
    notification.save()
    return Response({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_notification_count_api(request):
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    return Response({"count": count})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_add_lesson(request):
    Lesson.objects.create(
        title=request.data["title"],
        content=request.data.get("content", ""),
        course_id=request.data["course"],
        order=request.data["order"]
    )
    return Response({"success": True})

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTeacher])
def teacher_quizzes(request):
    quizzes = Quiz.objects.all()

    data = []
    for q in quizzes:
        data.append({
            "id": q.id,
            "title": q.title,
            "lesson_title": q.lesson.title,
            "question_count": q.questions.count(),
        })

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTeacher])
def teacher_students(request):
    enrollments = Enrollment.objects.select_related("student", "course")

    data = []
    for e in enrollments:
        total = Lesson.objects.filter(course=e.course).count()
        completed = Progress.objects.filter(
            student=e.student,
            lesson__course=e.course,
            completed=True
        ).count()

        progress = int((completed / total) * 100) if total else 0

        data.append({
            "student": e.student.user.username,
            "course": e.course.title,
            "progress": progress,
        })

    return Response(data)