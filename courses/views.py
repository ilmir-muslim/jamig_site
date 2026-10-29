from django.shortcuts import get_object_or_404, render

from .models import Course


def course_list(request):
    """Страница со списком опубликованных курсов, отсортированных по дате публикации."""
    courses = Course.objects.filter(status="published").order_by("-published_at")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, slug):
    """Страница конкретного курса с его уроками."""
    course = get_object_or_404(Course, slug=slug, status="published")
    lessons = course.lessons.all()  # type: ignore[attr-defined]
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "lessons": lessons,
        },
    )
