from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Student
from core.permissions import IsStudent
from .models import Certificate

from .models import (
    Course, Lesson, Enrollment, Progress,
    Quiz, Question, StudentAnswer
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
        data.append({
            "id": l.id,
            "title": l.title,
            "order": l.order,
            "unlocked": unlocked
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
    Check if a lesson is unlocked for the student.
    First lesson is always unlocked.
    Subsequent lessons require all previous lessons and their quizzes to be completed/passed.
    """
    # First lesson always unlocked
    if lesson.order == 1:
        return True

    # All previous lessons
    previous = Lesson.objects.filter(course=lesson.course, order__lt=lesson.order).order_by("order")

    for prev in previous:
        # Check if lesson is completed
        lesson_done = Progress.objects.filter(student=student, lesson=prev, completed=True).exists()

        # Check if quiz is passed (if quiz exists)
        quiz_done = True  # default True if no quiz
        if hasattr(prev, "quiz") and prev.quiz:
            quiz_done = Quiz.objects.filter(
                id=prev.quiz.id,
                id__in=student.completed_quizzes.values_list("id", flat=True)
            ).exists()

        # If either lesson or quiz not done → locked
        if not (lesson_done and quiz_done):
            return False

    return True


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def lesson_detail(request, lesson_id):
    student = request.user.student
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if not is_lesson_unlocked(student, lesson):
        return Response({"detail": "Locked"}, status=403)

    return Response(LessonSerializer(lesson).data)
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
        "locked": passed,
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

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def student_dashboard(request):
    student = request.user.student
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
@permission_classes([IsAuthenticated])
def submit_quiz(request, quiz_id):
    student = request.user.student
    quiz = get_object_or_404(Quiz, id=quiz_id)
    answers = request.data.get("answers", {})

    total = quiz.questions.count()
    if not answers:
        return Response({"error": "No answers submitted"}, status=400)

    correct = 0
    result = []

    # Evaluate answers
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

        # Save StudentAnswer
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
        # Mark current lesson as completed
        lesson = get_object_or_404(Lesson, quiz=quiz)
        Progress.objects.update_or_create(
            student=student,
            lesson=lesson,
            defaults={"completed": True}
        )

        # Try to find next lesson by order
        next_lesson = Lesson.objects.filter(
            course=lesson.course,
            order__gt=lesson.order
        ).order_by("order").first()

        # Fallback: if order is duplicate, pick by id
        if not next_lesson:
            next_lesson = Lesson.objects.filter(
                course=lesson.course,
                id__gt=lesson.id
            ).order_by("id").first()

        if next_lesson:
            next_lesson_id = next_lesson.id
        else:
            all_lessons_completed 
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
    
    verify_url = request.build_absolute_uri(
    reverse("verify_certificate", args=[certificate_obj.id])
   )
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
    progress.completed = True
    progress.save()

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
        # ❌ Invalid certificate
        return render(request, "courses/invalid_certificate.html")

    if certificate.is_revoked:
        # 🚫 Revoked certificate
        return render(request, "courses/revoked_certificate.html", {
            "certificate_id": certificate.id
        })

    # ✅ Valid certificate
    context = {
        "student": certificate.student.get_full_name() or certificate.student.username,
        "course": certificate.course.title,
        "issued_on": certificate.issued_at.strftime("%d %B %Y") if certificate.issued_at else "—",
        "certificate_id": certificate.id,
    }

    return render(request, "courses/verify_certificate.html", context)