from django.shortcuts import render, get_object_or_404
from .models import Course


def course_list(request):
    courses = Course.objects.filter(status="published").order_by("-published_at")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, status="published")
    lessons = course.lessons.all()
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "lessons": lessons,
        },
    )
